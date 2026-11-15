"""Conexão com o PostgreSQL a partir de variáveis de ambiente / arquivo .env."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent
DATABASE_DIR = ROOT / "database"


def load_env(path: Path = ROOT / ".env") -> None:
    """Carrega KEY=VALUE do .env sem sobrescrever variáveis já definidas no ambiente."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def connect(user_var: str = "POSTGRES_USER", password_var: str = "POSTGRES_PASSWORD",
            user: str | None = None, **kwargs) -> psycopg.Connection:
    load_env()
    missing = [v for v in ("POSTGRES_DB", password_var) + (() if user else (user_var,))
               if not os.environ.get(v)]
    if missing:
        raise SystemExit(f"Variáveis ausentes: {', '.join(missing)}. Copie .env.example para .env.")
    return psycopg.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ["POSTGRES_DB"],
        user=user or os.environ[user_var],
        password=os.environ[password_var],
        **kwargs,
    )


def run_script(conn: psycopg.Connection, filename: str):
    """Executa um script SQL de database/ (sem meta-comandos psql) e devolve o último resultado."""
    sql = "\n".join(
        line for line in (DATABASE_DIR / filename).read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("\\")
    )
    cur = conn.execute(sql)
    rows = None
    while True:
        if cur.description is not None:
            rows = cur.fetchall()
        if not cur.nextset():
            break
    return rows


def checksums(conn: psycopg.Connection) -> list[tuple[str, int, str]]:
    return run_script(conn, "checksums.sql")
