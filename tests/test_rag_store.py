"""Indexação incremental no PostgreSQL com embedder falso (sem API da OpenAI).

Cada teste usa um schema temporário dentro de uma transação que é desfeita no final, então
o schema rag real não é lido nem alterado. Pulado se o banco não estiver acessível.
"""

import copy
import hashlib
import random

import psycopg
import pytest
from psycopg import sql

from db import connect
from rag import embeddings, store
from rag.documents import build_documents, corpus_sha256, load_sources

try:
    _probe = connect(connect_timeout=3)
    _probe.close()
    DB_OK, DB_MOTIVO = True, ""
except (psycopg.OperationalError, SystemExit) as exc:
    DB_OK, DB_MOTIVO = False, f"banco indisponível: {exc}"

pytestmark = pytest.mark.skipif(not DB_OK, reason=DB_MOTIVO)

SCHEMA = "rag_test_tmp"
MODEL, DIMS = embeddings.MODEL, embeddings.DIMENSIONS


class FakeEmbedder:
    """Vetor determinístico derivado do texto; conta chamadas e textos recebidos."""

    def __init__(self):
        self.model, self.dimensions = MODEL, DIMS
        self.calls = []

    def embed(self, texts):
        self.calls.append(list(texts))
        vectors = []
        for t in texts:
            rnd = random.Random(hashlib.sha256(t.encode()).digest())
            vectors.append([rnd.uniform(-1, 1) for _ in range(DIMS)])
        return embeddings.EmbeddingResult(vectors=vectors, prompt_tokens=sum(len(t) // 4 for t in texts), model=MODEL)


class Factory:
    def __init__(self):
        self.embedder = FakeEmbedder()
        self.created = 0

    def __call__(self):
        self.created += 1
        return self.embedder


@pytest.fixture()
def conn():
    c = connect()
    try:
        yield c
    finally:
        c.rollback()
        c.close()


@pytest.fixture(scope="module")
def sources():
    return load_sources()


def run(conn, docs, factory):
    return store.index(conn, docs, factory, MODEL, DIMS, schema=SCHEMA)


def count(conn, table="documents"):
    return conn.execute(sql.SQL("SELECT count(*) FROM {}.{}").format(sql.Identifier(SCHEMA), sql.Identifier(table))).fetchone()[0]


def test_primeira_indexacao_e_idempotencia(conn, sources):
    docs = build_documents(*sources)
    f = Factory()
    r1 = run(conn, docs, f)
    assert len(r1.plan.new) == 24 and f.created == 1 and len(f.embedder.calls[0]) == 24
    assert count(conn) == 24

    f2 = Factory()
    r2 = run(conn, docs, f2)
    assert f2.created == 0, "documentos inalterados não podem gerar embeddings"
    assert len(r2.plan.unchanged) == 24 and r2.prompt_tokens == 0
    assert count(conn, "index_runs") == 2


def test_somente_documento_alterado_e_revetorizado(conn, sources):
    catalog, rules = copy.deepcopy(sources)
    run(conn, build_documents(catalog, rules), Factory())
    antes = dict(conn.execute(sql.SQL("SELECT doc_id, embedding_sha256 FROM {}.documents").format(sql.Identifier(SCHEMA))).fetchall())

    rules["regras"][0]["observacoes"] += " (alterado)"
    f = Factory()
    r = run(conn, build_documents(catalog, rules), f)
    assert [d.doc_id for d in r.plan.changed] == ["regra:R01"]
    assert f.embedder.calls == [[d.content for d in r.plan.changed]]
    # o hash do arquivo de regras muda nos metadados de todos os docs: atualizados sem embedding
    assert len(r.plan.metadata) == 23
    depois = dict(conn.execute(sql.SQL("SELECT doc_id, embedding_sha256 FROM {}.documents").format(sql.Identifier(SCHEMA))).fetchall())
    assert {k for k in antes if antes[k] != depois[k]} == {"regra:R01"}

    f3 = Factory()
    run(conn, build_documents(catalog, rules), f3)
    assert f3.created == 0


def test_documento_removido_e_apagado(conn, sources):
    catalog, rules = copy.deepcopy(sources)
    run(conn, build_documents(catalog, rules), Factory())
    rules["regras"] = [r for r in rules["regras"] if r["id"] != "R12"]
    for t in catalog["tabelas"]:      # remove referências para manter o catálogo coerente
        t["regras"] = [x for x in t.get("regras", []) if x != "R12"]
        for c in t["colunas"]:
            if "regras" in c:
                c["regras"] = [x for x in c["regras"] if x != "R12"]
    r = run(conn, build_documents(catalog, rules), Factory())
    assert r.plan.deleted == ["regra:R12"] and count(conn) == 23


def test_conteudo_hashes_e_vetores_gravados(conn, sources):
    docs = build_documents(*sources)
    f = Factory()
    run(conn, docs, f)
    rows = conn.execute(sql.SQL(
        "SELECT doc_id, doc_type, content, content_sha256, metadata, embedding::text, embedding_model, "
        "embedding_dimensions, embedding_sha256, vector_dims(embedding) FROM {}.documents").format(sql.Identifier(SCHEMA))).fetchall()
    by_id = {d.doc_id: d for d in docs}
    sent = dict(zip([d.doc_id for d in docs], f.embedder.calls[0]))
    for doc_id, doc_type, content, c_hash, meta, emb, model, dims, e_hash, vdims in rows:
        d = by_id[doc_id]
        assert (doc_type, content, c_hash, meta) == (d.doc_type, d.content, d.content_sha256, d.metadata)
        assert sent[doc_id] == content
        assert (model, dims, vdims) == (MODEL, DIMS, DIMS)
        v = store.parse_vector(emb)
        assert store.embedding_sha256(v) == e_hash          # hash confere com o vetor armazenado
        expected = f.embedder.embed([content]).vectors[0]
        assert v == store.to_float32(expected)


def test_status_e_corpus(conn, sources):
    docs = build_documents(*sources)
    run(conn, docs, Factory())
    st = store.status(conn, schema=SCHEMA)
    assert st["table_exists"] and sum(st["by_type"].values()) == 24
    assert st["by_type"] == {"regra": 12, "relacionamento": 5, "tabela": 6, "visao_geral": 1}
    assert st["stored_corpus_sha256"] == corpus_sha256(docs)
    assert st["last_run"][5] == corpus_sha256(docs) and st["n_runs"] == 1


def test_troca_de_modelo_revetoriza_tudo(conn, sources):
    docs = build_documents(*sources)
    run(conn, docs, Factory())
    p = store.plan(docs, store.fetch_existing(conn, SCHEMA), "outro-modelo", DIMS)
    assert len(p.changed) == 24


def test_falha_da_api_nao_grava_nada(conn, sources):
    docs = build_documents(*sources)

    def factory():
        raise embeddings.EmbeddingError("simulada")

    with pytest.raises(embeddings.EmbeddingError):
        run(conn, docs, factory)
    conn.rollback()
    assert not store.table_exists(conn, SCHEMA)


def test_schema_rag_real_nao_e_tocado(conn):
    """Os testes usam outro schema; a role somente leitura continua sem acesso a rag."""
    assert conn.execute("SELECT has_schema_privilege('nl2sql_readonly', 'rag', 'USAGE')").fetchone()[0] is False
