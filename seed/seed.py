"""Popula o schema `dataset` com o dataset sintético determinístico.

Uso (a partir da raiz do repositório):
    python seed/seed.py            # popula um schema vazio
    python seed/seed.py --reset    # esvazia as tabelas (TRUNCATE) e popula novamente
    python seed/seed.py --checksums  # apenas imprime os checksums do conteúdo atual

Conexão: variáveis POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER e
POSTGRES_PASSWORD (do ambiente ou do arquivo .env na raiz).
"""

from __future__ import annotations

import argparse
import sys
import time

from db import checksums, connect
from generator import COLUNAS, DATA_REFERENCIA, ORDEM_TABELAS, SEED, generate


def print_checksums(conn) -> None:
    print("\nChecksums do conteúdo (database/checksums.sql):")
    for tabela, linhas, md5 in checksums(conn):
        print(f"  {tabela:14s} {linhas:>7d}  {md5}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="TRUNCATE nas tabelas antes de popular")
    parser.add_argument("--checksums", action="store_true", help="somente imprime os checksums")
    args = parser.parse_args()

    with connect() as conn:
        exists = conn.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'dataset'"
        ).fetchone()[0]
        if exists != len(ORDEM_TABELAS):
            print("ERRO: schema 'dataset' incompleto. Rode database/schema.sql "
                  "(feito automaticamente pelo docker compose na primeira inicialização).")
            return 1

        if args.checksums:
            print_checksums(conn)
            return 0

        non_empty = [t for t in ORDEM_TABELAS
                     if conn.execute(f"SELECT EXISTS (SELECT 1 FROM dataset.{t})").fetchone()[0]]
        if non_empty and not args.reset:
            print(f"ERRO: tabelas já populadas ({', '.join(non_empty)}). Use --reset para recriar os dados.")
            return 1

        t0 = time.perf_counter()
        ds = generate(SEED)
        print(f"Dataset gerado (seed={SEED}, referência={DATA_REFERENCIA}) em {time.perf_counter() - t0:.1f}s")
        print(f"Digest do gerador: {ds.digest()}")

        with conn.transaction():
            if args.reset:
                conn.execute("TRUNCATE " + ", ".join(f"dataset.{t}" for t in ORDEM_TABELAS))
            with conn.cursor() as cur:
                for tabela in ORDEM_TABELAS:
                    cols = ", ".join(COLUNAS[tabela])
                    with cur.copy(f"COPY dataset.{tabela} ({cols}) FROM STDIN") as copy:
                        for row in ds.tables[tabela]:
                            copy.write_row(row)
                    print(f"  {tabela:14s} {len(ds.tables[tabela]):>7d} linhas")
        conn.execute("ANALYZE")  # fora da transação: atualiza estatísticas do planner
        print_checksums(conn)
    print("\nSeed concluído.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
