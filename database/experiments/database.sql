-- =============================================================================
-- TCC NL2SQL — Banco de registro dos experimentos (tcc_experiments)
--
-- Cria (ou atualiza) a role "experiment_writer" e o banco "tcc_experiments".
-- Idempotente. Executar como a role administrativa (superusuário do container),
-- conectado a qualquer banco (ex.: tcc_nl2sql). Em seguida execute schema.sql
-- conectado a tcc_experiments (docker/initdb/02_experiments.sql faz os dois).
--
-- Isolamento: a role nl2sql_readonly (usada pelas arquiteturas) NÃO recebe
-- CONNECT neste banco, portanto nenhuma arquitetura consegue ler perguntas,
-- SQL ou resultados registrados — o registro não pode virar gabarito.
--
-- A senha NÃO fica no repositório. Ela é lida, nesta ordem, de:
--   1. variável psql  -v experiment_password=...
--   2. variável de ambiente EXPERIMENT_WRITER_PASSWORD
-- =============================================================================

\set ON_ERROR_STOP on

\if :{?experiment_password}
\else
    \getenv experiment_password EXPERIMENT_WRITER_PASSWORD
\endif

\if :{?experiment_password}
\else
    DO $$ BEGIN RAISE EXCEPTION 'Defina EXPERIMENT_WRITER_PASSWORD (ou -v experiment_password=...)'; END $$;
\endif

SELECT 'CREATE ROLE experiment_writer'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'experiment_writer')
\gexec

ALTER ROLE experiment_writer WITH
    LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS
    CONNECTION LIMIT 10
    PASSWORD :'experiment_password';

SELECT 'CREATE DATABASE tcc_experiments'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'tcc_experiments')
\gexec

-- Por padrão o PostgreSQL concede CONNECT/TEMPORARY a PUBLIC: retira e libera
-- somente para a role de registro.
REVOKE ALL ON DATABASE tcc_experiments FROM PUBLIC;
GRANT CONNECT ON DATABASE tcc_experiments TO experiment_writer;
