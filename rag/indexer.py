"""CLI da indexação semântica dos metadados (arquitetura B).

    python -m rag.indexer --dry-run [--export docs.jsonl]   gera os documentos e mostra o plano (sem API, sem escrita)
    python -m rag.indexer --index                           cria as tabelas se preciso e vetoriza só o que mudou
    python -m rag.indexer --status                          estado de rag.documents e da última execução

Conexão: variáveis POSTGRES_* do .env (role administrativa). Chave: OPENAI_API_KEY ou OPENAI_API.
Somente --index acessa a API da OpenAI, e apenas se houver documentos novos ou alterados.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import psycopg

from . import embeddings, store
from .documents import BUILDER_VERSION, Document, corpus_sha256, load_documents

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "seed"))
from db import connect, load_env  # noqa: E402

ACTION_LABEL = {"new": "novo", "changed": "alterado", "metadata": "metadados", "unchanged": "inalterado",
                "deleted": "removido"}


def _connect_or_none():
    try:
        return connect(connect_timeout=5)
    except (psycopg.OperationalError, SystemExit) as exc:
        print(f"[aviso] banco indisponível ({exc}); plano calculado como se rag.documents estivesse vazio.")
        return None


def _print_header(docs: list[Document]) -> None:
    meta = docs[0].metadata
    print(f"Modelo de embeddings : {embeddings.MODEL} ({embeddings.DIMENSIONS} dimensões)")
    print(f"Versão do construtor : {BUILDER_VERSION}")
    print(f"schema_catalog.json  : sha256 {meta['schema_catalog_sha256']}")
    print(f"business_rules.json  : sha256 {meta['business_rules_sha256']}")
    print(f"Corpus ({len(docs)} docs)    : sha256 {corpus_sha256(docs)}")


def cmd_dry_run(args) -> int:
    docs = load_documents()
    conn = _connect_or_none()
    existing = {}
    if conn:
        with conn:
            existing = store.fetch_existing(conn)
            if not store.table_exists(conn):
                print("[info] rag.documents ainda não existe; será criada por --index.")
    p = store.plan(docs, existing, embeddings.MODEL, embeddings.DIMENSIONS)

    _print_header(docs)
    print()
    print(f"{'doc_id':<52} {'tipo':<15} {'chars':>6} {'~tokens':>8}  {'ação':<11} content_sha256")
    for d in docs:
        print(f"{d.doc_id:<52} {d.doc_type:<15} {len(d.content):>6} {embeddings.estimate_tokens(d.content):>8}  "
              f"{ACTION_LABEL[p.action(d.doc_id)]:<11} {d.content_sha256[:16]}…")
    for doc_id in p.deleted:
        print(f"{doc_id:<52} {'-':<15} {'-':>6} {'-':>8}  {'removido':<11}")

    total_tokens = sum(embeddings.estimate_tokens(d.content) for d in docs)
    embed_tokens = sum(embeddings.estimate_tokens(d.content) for d in p.to_embed)
    by_type = {t: sum(1 for d in docs if d.doc_type == t) for t in dict.fromkeys(d.doc_type for d in docs)}
    print()
    print(f"Documentos: {len(docs)} ({', '.join(f'{k}={v}' for k, v in by_type.items())})")
    print(f"Plano: {len(p.new)} novos, {len(p.changed)} alterados, {len(p.metadata)} só metadados, "
          f"{len(p.unchanged)} inalterados, {len(p.deleted)} removidos")
    print(f"Embeddings a gerar: {len(p.to_embed)}  (~{embed_tokens} tokens, "
          f"~US$ {embeddings.estimate_cost_usd(embed_tokens):.6f})")
    print(f"Corpus completo: ~{total_tokens} tokens, ~US$ {embeddings.estimate_cost_usd(total_tokens):.6f} "
          f"(estimativa conservadora, US$ {embeddings.PRICE_USD_PER_1M_TOKENS}/1M tokens)")
    print("Nenhuma chamada à API e nenhuma escrita no banco foram feitas (--dry-run).")

    if args.export:
        out = Path(args.export)
        with out.open("w", encoding="utf-8", newline="\n") as fh:
            for d in docs:
                fh.write(json.dumps({"doc_id": d.doc_id, "doc_type": d.doc_type, "title": d.title,
                                     "content_sha256": d.content_sha256, "metadata": d.metadata,
                                     "content": d.content}, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"Documentos exportados para {out}")
    return 0


def cmd_index(args) -> int:
    load_env()
    docs = load_documents()

    def factory():
        return embeddings.OpenAIEmbedder()

    with connect(connect_timeout=5) as conn:
        try:
            report = store.index(conn, docs, factory, embeddings.MODEL, embeddings.DIMENSIONS)
        except embeddings.EmbeddingError as exc:
            conn.rollback()
            print(f"[erro] {exc}\nNada foi gravado (transação desfeita).", file=sys.stderr)
            return 1
        conn.commit()
    p = report.plan
    _print_header(docs)
    print(f"\nExecução {report.run_id}: {len(p.to_embed)} embeddings gerados ({len(p.new)} novos, "
          f"{len(p.changed)} alterados), {len(p.metadata)} só metadados, {len(p.unchanged)} inalterados, "
          f"{len(p.deleted)} removidos.")
    if p.to_embed:
        print(f"Tokens consumidos (informados pela API): {report.prompt_tokens} "
              f"(~US$ {embeddings.estimate_cost_usd(report.prompt_tokens):.6f})")
    else:
        print("Nada a vetorizar: a API não foi chamada.")
    return 0


def cmd_status(args) -> int:
    docs = load_documents()
    with connect(connect_timeout=5) as conn:
        st = store.status(conn)
        existing = store.fetch_existing(conn)
    _print_header(docs)
    print()
    if not st["table_exists"]:
        print("rag.documents não existe. Execute --index para criar e indexar.")
        return 2
    total = sum(st["by_type"].values())
    print(f"rag.documents: {total} documentos ({', '.join(f'{k}={v}' for k, v in st['by_type'].items()) or 'vazia'})")
    for model, dims, n in st["models"]:
        print(f"  modelo {model}, {dims} dimensões: {n} documentos")
    print(f"Corpus armazenado: sha256 {st['stored_corpus_sha256']}")
    p = store.plan(docs, existing, embeddings.MODEL, embeddings.DIMENSIONS)
    in_sync = not (p.to_embed or p.metadata or p.deleted)
    print(f"Sincronizado com metadata/: {'sim' if in_sync else 'não'} "
          f"({len(p.new)} novos, {len(p.changed)} alterados, {len(p.metadata)} só metadados, "
          f"{len(p.unchanged)} inalterados, {len(p.deleted)} removidos)")
    if st["last_run"]:
        r = st["last_run"]
        print(f"Última execução: #{r[0]} em {r[1]:%Y-%m-%d %H:%M:%S %Z} — {r[2]}/{r[3]}, construtor v{r[4]}, "
              f"corpus {r[5][:16]}…, {r[6]} docs, {r[7]} vetorizados, {r[8]} metadados, {r[9]} inalterados, "
              f"{r[10]} removidos, {r[11]} tokens")
    print(f"Execuções registradas: {st['n_runs']}, tokens acumulados: {st['total_prompt_tokens']}")
    return 0 if in_sync else 2


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")   # console do Windows (cp1252) e acentos
    parser = argparse.ArgumentParser(prog="python -m rag.indexer", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="gera os documentos e mostra o plano, sem API nem escrita")
    mode.add_argument("--index", action="store_true", help="vetoriza documentos novos/alterados (usa a API da OpenAI)")
    mode.add_argument("--status", action="store_true", help="mostra o estado do índice (exit 2 se desatualizado)")
    parser.add_argument("--export", metavar="ARQUIVO.jsonl", help="com --dry-run: grava os documentos gerados em JSONL")
    args = parser.parse_args(argv)
    if args.export and not args.dry_run:
        parser.error("--export só pode ser usado com --dry-run")
    if args.dry_run:
        return cmd_dry_run(args)
    if args.index:
        return cmd_index(args)
    return cmd_status(args)


if __name__ == "__main__":
    raise SystemExit(main())
