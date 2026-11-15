-- Executado automaticamente apenas na primeira inicialização do volume, depois
-- de 01_init.sql. Cria a role experiment_writer e o banco tcc_experiments
-- (registro das execuções das arquiteturas). A senha vem de
-- EXPERIMENT_WRITER_PASSWORD.
--
-- Para um volume já existente, aplique manualmente (ver README, seção
-- "Registro dos experimentos"):
--   docker compose up -d db
--   docker exec tcc-nl2sql-db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/02_experiments.sql'
\set ON_ERROR_STOP on
\i /database/experiments/database.sql
\c tcc_experiments
\i /database/experiments/schema.sql
