-- =============================================================================
-- TCC NL2SQL — Role somente leitura para os experimentos
--
-- Cria (ou atualiza) a role de login "nl2sql_readonly" e aplica database/grants.sql.
-- Executar como a role administrativa (POSTGRES_USER), conectado ao banco tcc_nl2sql.
--
-- A senha NÃO fica no repositório. Ela é lida, nesta ordem, de:
--   1. variável psql  -v readonly_password=...
--   2. variável de ambiente NL2SQL_READONLY_PASSWORD
-- =============================================================================

\set ON_ERROR_STOP on

\if :{?readonly_password}
\else
    \getenv readonly_password NL2SQL_READONLY_PASSWORD
\endif

\if :{?readonly_password}
\else
    DO $$ BEGIN RAISE EXCEPTION 'Defina NL2SQL_READONLY_PASSWORD (ou -v readonly_password=...)'; END $$;
\endif

SELECT 'CREATE ROLE nl2sql_readonly'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nl2sql_readonly')
\gexec

ALTER ROLE nl2sql_readonly WITH
    LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS
    CONNECTION LIMIT 20
    PASSWORD :'readonly_password';

-- Padrões de sessão da role (facilitam o SQL gerado e limitam consultas longas).
-- Observação: default_transaction_read_only é uma camada extra; a proteção real
-- são os privilégios (a role só possui SELECT).
ALTER ROLE nl2sql_readonly SET search_path = dataset;
ALTER ROLE nl2sql_readonly SET default_transaction_read_only = on;
ALTER ROLE nl2sql_readonly SET statement_timeout = '30s';

\ir grants.sql
