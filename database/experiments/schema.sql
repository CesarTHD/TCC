-- =============================================================================
-- TCC NL2SQL — Schema "eval" do banco tcc_experiments
--
-- Idempotente. Executar como a role administrativa, conectado a tcc_experiments
-- (depois de database.sql).
--
-- Modelo:
--   eval.experiment  uma rodada de avaliação (configuração registrada)
--   eval.run         uma linha por requisição HTTP a /api/chat
--                    (inclui rodadas de esclarecimento e reenvios manuais)
--   views            operation_outcome (última tentativa de cada mensagem),
--                    conversation_outcome (estado final de cada conversa) e
--                    architecture_summary (resumo por experimento/arquitetura)
--
-- A role experiment_writer só tem SELECT e INSERT: o registro é append-only
-- (nenhuma linha é alterada ou apagada pela aplicação).
-- =============================================================================

\set ON_ERROR_STOP on

CREATE SCHEMA IF NOT EXISTS eval;
COMMENT ON SCHEMA eval IS 'Registro das execuções das arquiteturas NL2SQL (TCC).';

-- Somente o dono cria objetos; ninguém mais usa o schema public deste banco.
REVOKE ALL ON SCHEMA public FROM PUBLIC;

CREATE TABLE IF NOT EXISTS eval.experiment (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    label       text        NOT NULL,
    description text,
    -- modelo, temperatura, versão dos prompts/workflows, checksum do dataset...
    config      jsonb       NOT NULL DEFAULT '{}'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE eval.experiment IS 'Rodada de avaliação; eval.run.experiment_id referencia esta tabela.';

CREATE TABLE IF NOT EXISTS eval.run (
    request_id            uuid        PRIMARY KEY,
    operation_id          uuid        NOT NULL,
    attempt               integer     NOT NULL CHECK (attempt >= 1),
    conversation_id       uuid        NOT NULL,
    experiment_id         uuid        REFERENCES eval.experiment (id),
    question_id           text,
    architecture          text        NOT NULL CHECK (architecture IN ('baseline', 'contextual', 'multiagent')),

    -- Entrada
    message               text        NOT NULL,
    history_length        integer     NOT NULL,
    pending_clarification jsonb,

    -- Saída
    status                text        NOT NULL CHECK (status IN ('completed', 'clarification_required', 'error')),
    http_status           integer     NOT NULL,
    response_message      text        NOT NULL,
    generated_sql         text,
    clarification_id      text,
    clarification_question text,
    error_code            text,
    error_source          text        CHECK (error_source IN ('workflow', 'gateway', 'client')),
    error_details         text,

    -- Resultado tabular
    result_columns        jsonb,
    result_rows           jsonb,      -- primeiras N linhas (ver result_rows_truncated)
    row_count             integer,    -- linhas devolvidas pelo workflow
    total_rows            integer,    -- data.totalRows, se o workflow informou
    result_rows_truncated boolean     NOT NULL DEFAULT false,
    result_hash           text,       -- SHA-256 de {columns, rows} completos

    -- Medidas
    execution_time_ms     numeric,    -- informado pela arquitetura (metadata)
    gateway_latency_ms    numeric     NOT NULL,  -- medido pela rota /api/chat (rede + n8n)
    sql_attempts          integer,    -- metadata.attempts
    context_used          jsonb,      -- metadata.contextUsed
    metadata              jsonb,      -- metadata completo devolvido pelo workflow
    response_json         jsonb       NOT NULL,  -- resposta validada (linhas limitadas a N)

    created_at            timestamptz NOT NULL DEFAULT now()
);
COMMENT ON TABLE eval.run IS 'Uma linha por requisição HTTP recebida por /api/chat.';
COMMENT ON COLUMN eval.run.operation_id IS 'Igual entre reenvios manuais da mesma mensagem.';
COMMENT ON COLUMN eval.run.gateway_latency_ms IS 'Tempo entre o recebimento na rota e o fim da resposta do n8n; não é o tempo interno da arquitetura.';

CREATE INDEX IF NOT EXISTS run_experiment_arch_idx ON eval.run (experiment_id, architecture);
CREATE INDEX IF NOT EXISTS run_conversation_idx   ON eval.run (conversation_id, created_at);
CREATE INDEX IF NOT EXISTS run_operation_idx      ON eval.run (operation_id, attempt);
CREATE INDEX IF NOT EXISTS run_created_idx        ON eval.run (created_at);

-- Último resultado de cada mensagem do usuário (desconsidera tentativas anteriores).
CREATE OR REPLACE VIEW eval.operation_outcome AS
SELECT DISTINCT ON (operation_id) *
FROM eval.run
ORDER BY operation_id, attempt DESC, created_at DESC;
COMMENT ON VIEW eval.operation_outcome IS 'Última tentativa de cada operação (mensagem do usuário).';

-- Estado final de cada conversa (uma pergunta de avaliação = uma conversa),
-- com quantas requisições e rodadas de esclarecimento foram necessárias.
DROP VIEW IF EXISTS eval.architecture_summary;
DROP VIEW IF EXISTS eval.conversation_outcome;
CREATE VIEW eval.conversation_outcome AS
SELECT DISTINCT ON (r.conversation_id)
    r.experiment_id,
    r.architecture,
    r.conversation_id,
    r.question_id,
    first_msg.message            AS original_question,
    r.status                     AS final_status,
    r.error_code,
    r.error_source,
    r.generated_sql,
    r.row_count,
    r.result_hash,
    r.execution_time_ms          AS final_execution_time_ms,
    agg.requests,
    agg.clarification_rounds,
    agg.total_gateway_latency_ms,
    first_msg.created_at         AS started_at,
    r.created_at                 AS finished_at
FROM eval.run r
CROSS JOIN LATERAL (
    SELECT count(*)                                              AS requests,
           count(*) FILTER (WHERE x.status = 'clarification_required') AS clarification_rounds,
           sum(x.gateway_latency_ms)                             AS total_gateway_latency_ms
    FROM eval.run x WHERE x.conversation_id = r.conversation_id
) agg
CROSS JOIN LATERAL (
    SELECT y.message, y.created_at FROM eval.run y
    WHERE y.conversation_id = r.conversation_id
    ORDER BY y.created_at LIMIT 1
) first_msg
ORDER BY r.conversation_id, r.created_at DESC;
COMMENT ON VIEW eval.conversation_outcome IS 'Estado final de cada conversa; use uma conversa por pergunta de avaliação.';

-- Resumo por experimento e arquitetura, por conversa (pergunta).
CREATE VIEW eval.architecture_summary AS
SELECT
    experiment_id,
    architecture,
    count(*)                                                          AS conversations,
    count(*) FILTER (WHERE final_status = 'completed')                AS completed,
    count(*) FILTER (WHERE final_status = 'clarification_required')   AS ended_awaiting_clarification,
    count(*) FILTER (WHERE final_status = 'error')                    AS errors,
    count(*) FILTER (WHERE final_status = 'error' AND error_source = 'gateway') AS integration_errors,
    avg(clarification_rounds)                                         AS avg_clarification_rounds,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY total_gateway_latency_ms) AS median_total_latency_ms,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY final_execution_time_ms)  AS median_final_execution_time_ms
FROM eval.conversation_outcome
GROUP BY experiment_id, architecture;

GRANT USAGE ON SCHEMA eval TO experiment_writer;
GRANT SELECT, INSERT ON eval.experiment, eval.run TO experiment_writer;
GRANT SELECT ON eval.operation_outcome, eval.conversation_outcome, eval.architecture_summary TO experiment_writer;

ALTER ROLE experiment_writer IN DATABASE tcc_experiments SET search_path = eval;
ALTER ROLE experiment_writer IN DATABASE tcc_experiments SET statement_timeout = '10s';
