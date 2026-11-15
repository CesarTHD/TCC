"""Testes contra o banco populado (pulados se o banco não estiver acessível).

Requer as variáveis do .env (POSTGRES_* e NL2SQL_READONLY_PASSWORD) e que o
seed já tenha sido executado.
"""

import json
import re

import psycopg
import pytest
from psycopg import errors

from db import ROOT, connect, run_script
from generator import COLUNAS, ORDEM_TABELAS

try:
    _probe = connect(connect_timeout=3)
    _probe.close()
    DB_OK, DB_MOTIVO = True, ""
except (psycopg.OperationalError, SystemExit) as exc:
    DB_OK, DB_MOTIVO = False, f"banco indisponível: {exc}"

pytestmark = pytest.mark.skipif(not DB_OK, reason=DB_MOTIVO)


@pytest.fixture(scope="module")
def admin():
    with connect() as conn:
        yield conn


@pytest.fixture()
def readonly():
    conn = connect(user="nl2sql_readonly", password_var="NL2SQL_READONLY_PASSWORD", autocommit=True)
    yield conn
    conn.close()


def test_conteudo_do_banco_igual_ao_gerador(admin, dataset):
    """O banco contém exatamente as linhas produzidas pelo gerador com seed 42."""
    for tabela in ORDEM_TABELAS:
        cols = ", ".join(COLUNAS[tabela])
        rows = admin.execute(f"SELECT {cols} FROM dataset.{tabela} ORDER BY id").fetchall()
        assert rows == dataset.tables[tabela], tabela


def test_validation_sql_sem_violacoes(admin):
    run_script(admin, "validation.sql")  # o bloco DO final levanta exceção se houver violação
    falhas = admin.execute("SELECT verificacao FROM validacao WHERE ocorrencias <> 0").fetchall()
    assert falhas == []


def test_readonly_select(readonly):
    assert readonly.execute("SHOW search_path").fetchone()[0] == "dataset"
    assert readonly.execute("SELECT count(*) FROM pedidos").fetchone()[0] > 0
    assert readonly.execute(
        "SELECT count(*) FROM dataset.itens_pedido i JOIN dataset.produtos p ON p.id = i.produto_id"
    ).fetchone()[0] > 0


@pytest.mark.parametrize("sql", [
    "INSERT INTO dataset.categorias (id, nome, descricao) VALUES (999, 'x', 'x')",
    "UPDATE dataset.pedidos SET status = 'CANCELADO' WHERE id = 1",
    "DELETE FROM dataset.itens_pedido WHERE id = 1",
    "TRUNCATE dataset.itens_pedido",
    "DROP TABLE dataset.itens_pedido",
    "ALTER TABLE dataset.pedidos ADD COLUMN x int",
    "CREATE TABLE dataset.x (id int)",
    "CREATE TABLE public.x (id int)",
    "CREATE TEMP TABLE x (id int)",
    "CREATE SCHEMA x",
])
def test_readonly_nao_modifica(readonly, sql):
    with pytest.raises((errors.InsufficientPrivilege, errors.ReadOnlySqlTransaction)):
        readonly.execute(sql)


def test_readonly_sem_privilegio_mesmo_fora_de_transacao_readonly(readonly):
    """Mesmo desligando default_transaction_read_only, faltam privilégios de escrita."""
    readonly.execute("SET default_transaction_read_only = off")
    for sql in (
        "INSERT INTO dataset.categorias (id, nome, descricao) VALUES (999, 'x', 'x')",
        "UPDATE dataset.pedidos SET status = 'CANCELADO' WHERE id = 1",
        "DELETE FROM dataset.itens_pedido WHERE id = 1",
        "TRUNCATE dataset.itens_pedido",
        "DROP TABLE dataset.itens_pedido",
        "ALTER TABLE dataset.pedidos ADD COLUMN x int",
        "CREATE TABLE dataset.x (id int)",
        "CREATE TABLE public.x (id int)",
        "CREATE TEMP TABLE x (id int)",
        "CREATE SCHEMA x",
    ):
        with pytest.raises(errors.InsufficientPrivilege):
            readonly.execute(sql)


def test_catalogo_corresponde_ao_schema(admin):
    catalogo = json.loads((ROOT / "metadata" / "schema_catalog.json").read_text(encoding="utf-8"))
    real = {}
    for tabela, coluna, tipo in admin.execute("""
        SELECT c.table_name, c.column_name,
               format_type(a.atttypid, a.atttypmod)
        FROM information_schema.columns c
        JOIN pg_attribute a ON a.attrelid = ('dataset.' || c.table_name)::regclass
                           AND a.attname = c.column_name
        WHERE c.table_schema = 'dataset' ORDER BY c.table_name, c.ordinal_position"""):
        real.setdefault(tabela, []).append((coluna, tipo))
    doc = {t["nome"]: [(c["nome"], c["tipo"]) for c in t["colunas"]] for t in catalogo["tabelas"]}
    assert doc == real


def test_valores_categoricos_do_catalogo_existem_no_banco(admin):
    catalogo = json.loads((ROOT / "metadata" / "schema_catalog.json").read_text(encoding="utf-8"))
    for t in catalogo["tabelas"]:
        for c in t["colunas"]:
            if "valores_possiveis" not in c:
                continue
            valores = {str(v) for (v,) in admin.execute(
                f"SELECT DISTINCT {c['nome']}::text FROM dataset.{t['nome']}")}
            esperado = {str(v["valor"]) for v in c["valores_possiveis"]}
            assert valores <= esperado, f"{t['nome']}.{c['nome']}"


def test_regras_de_negocio_referenciam_colunas_reais(admin):
    """Toda referência tabela.coluna nas regras de negócio existe no schema real."""
    regras = json.loads((ROOT / "metadata" / "business_rules.json").read_text(encoding="utf-8"))
    colunas = {f"{t}.{c}" for t, c in admin.execute(
        "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'dataset'")}
    tabelas = {c.split(".")[0] for c in colunas}
    for r in regras["regras"]:
        texto = " ".join(str(v) for k, v in r.items() if k in ("definicao_sql", "colunas"))
        for ref in re.findall(r"\b([a-z_]+)\.([a-z_]+)\b", texto):
            if ref[0] in tabelas:
                assert f"{ref[0]}.{ref[1]}" in colunas, (r["id"], ref)
        assert set(r["tabelas"]) <= tabelas, r["id"]
