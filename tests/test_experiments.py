"""Banco de registro dos experimentos (tcc_experiments): permissões e isolamento.

Pulados se o banco não estiver acessível ou se EXPERIMENT_WRITER_PASSWORD não
estiver no .env (ver database/experiments/ e docker/initdb/02_experiments.sql).
"""

import os
import uuid

import psycopg
import pytest
from psycopg import errors

from db import load_env

load_env()


def _connect(user: str, password_var: str, dbname: str, **kwargs) -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=dbname,
        user=user,
        password=os.environ[password_var],
        connect_timeout=3,
        **kwargs,
    )


def _writer(**kwargs):
    return _connect("experiment_writer", "EXPERIMENT_WRITER_PASSWORD", "tcc_experiments", **kwargs)


def _admin():
    return _connect(os.environ["POSTGRES_USER"], "POSTGRES_PASSWORD", "tcc_experiments", autocommit=True)


try:
    if not os.environ.get("EXPERIMENT_WRITER_PASSWORD"):
        raise SystemExit("EXPERIMENT_WRITER_PASSWORD ausente no .env")
    _writer().close()
    DB_OK, DB_MOTIVO = True, ""
except (psycopg.OperationalError, SystemExit, KeyError) as exc:
    DB_OK, DB_MOTIVO = False, f"tcc_experiments indisponível: {exc}"

pytestmark = pytest.mark.skipif(not DB_OK, reason=DB_MOTIVO)


def _insert_run(conn, experiment_id=None):
    request_id = uuid.uuid4()
    conn.execute(
        """INSERT INTO eval.run (request_id, operation_id, attempt, conversation_id, experiment_id,
               architecture, message, history_length, status, http_status, response_message,
               gateway_latency_ms, response_json)
           VALUES (%s, %s, 1, %s, %s, 'baseline', 'teste automatizado', 0, 'completed', 200, 'ok', 1, '{}')""",
        (request_id, uuid.uuid4(), uuid.uuid4(), experiment_id),
    )
    return request_id


def test_readonly_nao_conecta_no_banco_de_experimentos():
    with pytest.raises(psycopg.OperationalError, match="CONNECT"):
        _connect("nl2sql_readonly", "NL2SQL_READONLY_PASSWORD", "tcc_experiments").close()


def test_writer_nao_le_o_dataset():
    with _connect("experiment_writer", "EXPERIMENT_WRITER_PASSWORD", os.environ["POSTGRES_DB"]) as conn:
        with pytest.raises(errors.InsufficientPrivilege):
            conn.execute("SELECT count(*) FROM dataset.clientes")


def test_writer_insere_e_le_mas_nao_altera_nem_apaga():
    with _writer() as conn:
        assert conn.execute("SHOW search_path").fetchone()[0] == "eval"
        # Tudo dentro de uma transação desfeita ao final: nada fica gravado.
        request_id = _insert_run(conn)
        assert conn.execute("SELECT count(*) FROM eval.run WHERE request_id = %s", (request_id,)).fetchone()[0] == 1
        conn.rollback()
        for sql in ("UPDATE eval.run SET status = 'error'", "DELETE FROM eval.run", "TRUNCATE eval.run"):
            with pytest.raises(errors.InsufficientPrivilege):
                conn.execute(sql)
            conn.rollback()


def test_experimento_inexistente_e_rejeitado():
    with _writer() as conn:
        with pytest.raises(errors.ForeignKeyViolation):
            _insert_run(conn, experiment_id=uuid.uuid4())
        conn.rollback()


def test_views_de_analise_existem():
    with _admin() as conn:
        views = {r[0] for r in conn.execute(
            "SELECT table_name FROM information_schema.views WHERE table_schema = 'eval'")}
    assert {"operation_outcome", "conversation_outcome", "architecture_summary"} <= views
