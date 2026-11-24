-- =============================================================================
-- TCC NL2SQL — Role rag_reader (leitura do índice semântico da arquitetura B)
--
-- Usada SOMENTE pelo nó de busca vetorial do workflow B no n8n. Separada de
-- nl2sql_readonly para que o SQL gerado pela LLM continue sem acesso ao schema
-- rag, e para que a busca não tenha acesso ao schema dataset.
--
--   pode : CONNECT em tcc_nl2sql, USAGE em rag, SELECT em rag.documents
--   não  : dataset, rag.index_runs, escrita/DDL, tcc_experiments
--
-- Idempotente. Execute como administrador, conectado a tcc_nl2sql, com a senha em
-- RAG_READER_PASSWORD (ou -v rag_reader_password=...):
--   docker exec -e RAG_READER_PASSWORD=... tcc-nl2sql-db sh -c \
--     'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /database/rag_reader.sql'
-- Requer rag.documents (criada por python -m rag.indexer --index).
-- =============================================================================

\set ON_ERROR_STOP on

\if :{?rag_reader_password}
\else
    \getenv rag_reader_password RAG_READER_PASSWORD
\endif
\if :{?rag_reader_password}
\else
    DO $$ BEGIN RAISE EXCEPTION 'Defina RAG_READER_PASSWORD (ou -v rag_reader_password=...)'; END $$;
\endif

SELECT 'CREATE ROLE rag_reader'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'rag_reader')
\gexec

ALTER ROLE rag_reader WITH
    LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS
    CONNECTION LIMIT 10
    PASSWORD :'rag_reader_password';

ALTER ROLE rag_reader SET search_path = rag, public;
ALTER ROLE rag_reader SET default_transaction_read_only = on;
ALTER ROLE rag_reader SET statement_timeout = '10s';

SELECT format('GRANT CONNECT ON DATABASE %I TO rag_reader', current_database()) \gexec
REVOKE ALL ON SCHEMA rag FROM rag_reader;
GRANT USAGE ON SCHEMA rag TO rag_reader;
REVOKE ALL ON ALL TABLES IN SCHEMA rag FROM rag_reader;
GRANT SELECT ON rag.documents TO rag_reader;
