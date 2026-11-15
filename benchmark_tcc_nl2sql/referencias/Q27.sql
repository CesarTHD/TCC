-- Q27 — Qual foi a participação percentual de cada canal no faturamento de pedidos CONCLUIDOS de 2025 e a participação acumulada? Ordene os canais por faturamento decrescente e, em empate, por nome crescente. Arredonde os percentuais para duas casas.
WITH receita_canal AS (
    SELECT canal_venda,
           SUM(valor_total) AS faturamento
    FROM dataset.pedidos
    WHERE status = 'CONCLUIDO'
      AND data_pedido >= DATE '2025-01-01'
      AND data_pedido < DATE '2026-01-01'
    GROUP BY canal_venda
), participacao AS (
    SELECT canal_venda, faturamento,
           ROUND(100.0 * faturamento / NULLIF(SUM(faturamento) OVER (), 0), 2) AS participacao_pct,
           ROUND(100.0 * SUM(faturamento) OVER (
               ORDER BY faturamento DESC, canal_venda ASC
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
           ) / NULLIF(SUM(faturamento) OVER (), 0), 2) AS participacao_acumulada_pct
    FROM receita_canal
)
SELECT canal_venda, faturamento, participacao_pct, participacao_acumulada_pct
FROM participacao
ORDER BY faturamento DESC, canal_venda ASC;
