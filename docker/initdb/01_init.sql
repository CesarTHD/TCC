-- Executado automaticamente pelo entrypoint oficial do PostgreSQL apenas na
-- primeira inicialização do volume, conectado ao banco POSTGRES_DB como
-- POSTGRES_USER. A senha da role somente leitura vem da variável de ambiente
-- NL2SQL_READONLY_PASSWORD (lida por roles.sql via \getenv).
\set ON_ERROR_STOP on
\i /database/schema.sql
\i /database/roles.sql
