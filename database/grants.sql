-- =============================================================================
-- TCC NL2SQL — Privilégios da role nl2sql_readonly
--
-- Idempotente. Executado por roles.sql e por reset.sql (ao recriar o schema os
-- privilégios sobre as tabelas precisam ser reaplicados).
-- Pré-requisito: a role nl2sql_readonly já existe (database/roles.sql).
-- =============================================================================

\set ON_ERROR_STOP on

-- Ninguém além do dono cria objetos no schema public nem tabelas temporárias.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
SELECT format('REVOKE TEMPORARY ON DATABASE %I FROM PUBLIC', current_database()) \gexec
SELECT format('REVOKE CREATE ON DATABASE %I FROM PUBLIC', current_database()) \gexec

-- Conexão ao banco e leitura do schema dataset
SELECT format('GRANT CONNECT ON DATABASE %I TO nl2sql_readonly', current_database()) \gexec
REVOKE ALL ON SCHEMA dataset FROM nl2sql_readonly;
GRANT USAGE ON SCHEMA dataset TO nl2sql_readonly;
REVOKE ALL ON ALL TABLES IN SCHEMA dataset FROM nl2sql_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA dataset TO nl2sql_readonly;

-- Tabelas criadas futuramente no schema também ficam apenas com SELECT
ALTER DEFAULT PRIVILEGES IN SCHEMA dataset GRANT SELECT ON TABLES TO nl2sql_readonly;
