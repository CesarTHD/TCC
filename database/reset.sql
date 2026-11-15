-- =============================================================================
-- TCC NL2SQL — Reset do dataset
--
-- Remove o schema "dataset" (tabelas + dados) e o recria vazio, reaplicando os
-- privilégios da role nl2sql_readonly. A role em si não é removida.
-- Depois do reset, popular novamente com:  python seed/seed.py
--
-- Executar como a role administrativa, conectado ao banco tcc_nl2sql.
-- =============================================================================

\set ON_ERROR_STOP on

DROP SCHEMA IF EXISTS dataset CASCADE;

\ir schema.sql
\ir grants.sql

\echo 'Schema dataset recriado vazio. Execute o seed novamente.'
