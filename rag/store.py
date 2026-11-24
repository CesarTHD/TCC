"""Tabelas do RAG no PostgreSQL (pgvector) e indexação incremental.

rag.documents   um documento semântico por linha: texto, metadados JSONB, embedding e hashes
rag.index_runs  uma linha por execução de --index (modelo, dimensões, hashes, tokens consumidos)

Regra de idempotência (plan()):
    novo / alterado  -> gera embedding   (doc ausente, ou hash do texto, modelo ou dimensão diferente)
    metadados        -> só UPDATE        (texto igual; metadados, título ou tipo diferentes)
    inalterado       -> nada
    removido         -> DELETE           (doc no banco que não é mais gerado pelos metadados)

O schema é parametrizável apenas para os testes, que usam um schema temporário.
"""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass, field

from psycopg import sql

from .documents import BUILDER_VERSION, DOC_TYPES, Document, corpus_sha256
from .embeddings import DIMENSIONS

SCHEMA = "rag"
LOCK_KEY = 0x7261675F696478  # "rag_idx": impede duas indexações simultâneas


def ddl(schema: str = SCHEMA, dimensions: int = DIMENSIONS) -> sql.Composed:
    types = sql.SQL(", ").join(sql.Literal(t) for t in DOC_TYPES)
    return sql.SQL("""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE SCHEMA IF NOT EXISTS {s};

CREATE TABLE IF NOT EXISTS {s}.documents (
    doc_id               text PRIMARY KEY,
    doc_type             text NOT NULL CHECK (doc_type IN ({types})),
    title                text NOT NULL,
    content              text NOT NULL,
    content_sha256       char(64) NOT NULL,
    metadata             jsonb NOT NULL,
    embedding            vector({dim}) NOT NULL,
    embedding_model      text NOT NULL,
    embedding_dimensions integer NOT NULL CHECK (embedding_dimensions = {dim}),
    embedding_sha256     char(64) NOT NULL,
    embedded_at          timestamptz NOT NULL DEFAULT now(),
    updated_at           timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE {s}.documents IS
    'Documentos semânticos gerados de metadata/*.json para o RAG da arquitetura B (rag/documents.py).';
COMMENT ON COLUMN {s}.documents.content_sha256 IS 'SHA-256 do texto (UTF-8) enviado ao modelo de embeddings.';
COMMENT ON COLUMN {s}.documents.embedding_sha256 IS 'SHA-256 do vetor como float32 little-endian.';

CREATE TABLE IF NOT EXISTS {s}.index_runs (
    id                     bigserial PRIMARY KEY,
    executed_at            timestamptz NOT NULL DEFAULT now(),
    embedding_model        text NOT NULL,
    embedding_dimensions   integer NOT NULL,
    builder_version        text NOT NULL,
    corpus_sha256          char(64) NOT NULL,
    schema_catalog_sha256  char(64) NOT NULL,
    business_rules_sha256  char(64) NOT NULL,
    n_documents            integer NOT NULL,
    n_embedded             integer NOT NULL,
    n_metadata_updated     integer NOT NULL,
    n_unchanged            integer NOT NULL,
    n_deleted              integer NOT NULL,
    prompt_tokens          integer NOT NULL,
    embedded_doc_ids       text[] NOT NULL,
    deleted_doc_ids        text[] NOT NULL
);
COMMENT ON TABLE {s}.index_runs IS 'Histórico das execuções de python -m rag.indexer --index.';
""").format(s=sql.Identifier(schema), types=types, dim=sql.Literal(dimensions))


# --------------------------------------------------------------------------- vetores

def to_float32(vector: list[float]) -> list[float]:
    """Arredonda para float32, a precisão armazenada pelo pgvector."""
    return list(struct.unpack(f"<{len(vector)}f", struct.pack(f"<{len(vector)}f", *vector)))


def embedding_sha256(vector: list[float]) -> str:
    return hashlib.sha256(struct.pack(f"<{len(vector)}f", *vector)).hexdigest()


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(repr(x) for x in vector) + "]"


def parse_vector(text: str) -> list[float]:
    """Texto do pgvector ('[0.47951263,...]', float32 em forma curta) -> valores float32 exatos."""
    return to_float32([float(x) for x in text.strip("[]").split(",")])


# --------------------------------------------------------------------------- leitura

def table_exists(conn, schema: str = SCHEMA) -> bool:
    return conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"{schema}.documents",)).fetchone()[0]


def fetch_existing(conn, schema: str = SCHEMA) -> dict[str, dict]:
    if not table_exists(conn, schema):
        return {}
    rows = conn.execute(sql.SQL(
        "SELECT doc_id, doc_type, title, content_sha256, metadata, embedding_model, embedding_dimensions "
        "FROM {}.documents").format(sql.Identifier(schema))).fetchall()
    return {r[0]: {"doc_type": r[1], "title": r[2], "content_sha256": r[3], "metadata": r[4],
                   "embedding_model": r[5], "embedding_dimensions": r[6]} for r in rows}


# --------------------------------------------------------------------------- plano

@dataclass
class Plan:
    new: list[Document] = field(default_factory=list)
    changed: list[Document] = field(default_factory=list)
    metadata: list[Document] = field(default_factory=list)
    unchanged: list[Document] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)

    @property
    def to_embed(self) -> list[Document]:
        return self.new + self.changed

    def action(self, doc_id: str) -> str:
        for name in ("new", "changed", "metadata", "unchanged"):
            if any(d.doc_id == doc_id for d in getattr(self, name)):
                return name
        return "deleted" if doc_id in self.deleted else "?"


def plan(docs: list[Document], existing: dict[str, dict], model: str, dimensions: int) -> Plan:
    p = Plan()
    for d in docs:
        row = existing.get(d.doc_id)
        if row is None:
            p.new.append(d)
        elif (row["content_sha256"] != d.content_sha256 or row["embedding_model"] != model
              or row["embedding_dimensions"] != dimensions):
            p.changed.append(d)
        elif row["metadata"] != d.metadata or row["title"] != d.title or row["doc_type"] != d.doc_type:
            p.metadata.append(d)
        else:
            p.unchanged.append(d)
    current = {d.doc_id for d in docs}
    p.deleted = sorted(doc_id for doc_id in existing if doc_id not in current)
    return p


# --------------------------------------------------------------------------- escrita

@dataclass
class IndexReport:
    plan: Plan
    prompt_tokens: int
    corpus_sha256: str
    run_id: int


def index(conn, docs: list[Document], embedder_factory, model: str, dimensions: int,
          schema: str = SCHEMA) -> IndexReport:
    """Indexa de forma incremental, em uma única transação (o chamador faz commit/rollback).

    embedder_factory só é chamado se houver documentos a vetorizar, então uma execução sem
    mudanças não exige chave nem acessa a API.
    """
    s = sql.Identifier(schema)
    conn.execute(ddl(schema, dimensions))
    conn.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_KEY,))
    p = plan(docs, fetch_existing(conn, schema), model, dimensions)

    tokens = 0
    if p.to_embed:
        embedder = embedder_factory()
        if embedder.model != model or embedder.dimensions != dimensions:
            raise ValueError("embedder com modelo/dimensão diferente do plano")
        result = embedder.embed([d.content for d in p.to_embed])
        tokens = result.prompt_tokens
        upsert = sql.SQL("""
            INSERT INTO {s}.documents (doc_id, doc_type, title, content, content_sha256, metadata, embedding,
                                       embedding_model, embedding_dimensions, embedding_sha256, embedded_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::vector, %s, %s, %s, now(), now())
            ON CONFLICT (doc_id) DO UPDATE SET
                doc_type = EXCLUDED.doc_type, title = EXCLUDED.title, content = EXCLUDED.content,
                content_sha256 = EXCLUDED.content_sha256, metadata = EXCLUDED.metadata,
                embedding = EXCLUDED.embedding, embedding_model = EXCLUDED.embedding_model,
                embedding_dimensions = EXCLUDED.embedding_dimensions,
                embedding_sha256 = EXCLUDED.embedding_sha256, embedded_at = now(), updated_at = now()
        """).format(s=s)
        for d, vec in zip(p.to_embed, result.vectors, strict=True):
            v32 = to_float32(vec)
            conn.execute(upsert, (d.doc_id, d.doc_type, d.title, d.content, d.content_sha256, d.metadata_json,
                                  vector_literal(v32), model, dimensions, embedding_sha256(v32)))

    for d in p.metadata:
        conn.execute(sql.SQL("UPDATE {s}.documents SET doc_type = %s, title = %s, metadata = %s::jsonb, "
                             "updated_at = now() WHERE doc_id = %s").format(s=s),
                     (d.doc_type, d.title, d.metadata_json, d.doc_id))
    if p.deleted:
        conn.execute(sql.SQL("DELETE FROM {s}.documents WHERE doc_id = ANY(%s)").format(s=s), (p.deleted,))

    corpus = corpus_sha256(docs)
    meta = docs[0].metadata if docs else {}
    run_id = conn.execute(sql.SQL("""
        INSERT INTO {s}.index_runs (embedding_model, embedding_dimensions, builder_version, corpus_sha256,
            schema_catalog_sha256, business_rules_sha256, n_documents, n_embedded, n_metadata_updated,
            n_unchanged, n_deleted, prompt_tokens, embedded_doc_ids, deleted_doc_ids)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
    """).format(s=s), (model, dimensions, BUILDER_VERSION, corpus, meta.get("schema_catalog_sha256", ""),
                       meta.get("business_rules_sha256", ""), len(docs), len(p.to_embed), len(p.metadata),
                       len(p.unchanged), len(p.deleted), tokens, [d.doc_id for d in p.to_embed], p.deleted)
    ).fetchone()[0]
    return IndexReport(plan=p, prompt_tokens=tokens, corpus_sha256=corpus, run_id=run_id)


# --------------------------------------------------------------------------- status

def status(conn, schema: str = SCHEMA) -> dict:
    if not table_exists(conn, schema):
        return {"table_exists": False}
    s = sql.Identifier(schema)
    by_type = dict(conn.execute(sql.SQL(
        "SELECT doc_type, count(*) FROM {s}.documents GROUP BY 1 ORDER BY 1").format(s=s)).fetchall())
    models = conn.execute(sql.SQL(
        "SELECT embedding_model, embedding_dimensions, count(*) FROM {s}.documents GROUP BY 1, 2 ORDER BY 1, 2"
    ).format(s=s)).fetchall()
    # ordenado em Python (a collation do banco pode ordenar diferente), como em corpus_sha256()
    pairs = sorted(conn.execute(sql.SQL("SELECT doc_id, content_sha256 FROM {s}.documents").format(s=s)).fetchall())
    stored_corpus = hashlib.sha256("\n".join(f"{i}\t{h}" for i, h in pairs).encode("utf-8")).hexdigest() if pairs else None
    last = conn.execute(sql.SQL(
        "SELECT id, executed_at, embedding_model, embedding_dimensions, builder_version, corpus_sha256, n_documents, "
        "n_embedded, n_metadata_updated, n_unchanged, n_deleted, prompt_tokens FROM {s}.index_runs "
        "ORDER BY id DESC LIMIT 1").format(s=s)).fetchone()
    totals = conn.execute(sql.SQL(
        "SELECT count(*), coalesce(sum(prompt_tokens), 0) FROM {s}.index_runs").format(s=s)).fetchone()
    return {"table_exists": True, "by_type": by_type, "models": models, "stored_corpus_sha256": stored_corpus,
            "last_run": last, "n_runs": totals[0], "total_prompt_tokens": totals[1]}
