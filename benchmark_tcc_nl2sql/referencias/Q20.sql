-- Q20 — Qual foi a taxa percentual de cancelamento por canal de venda em 2025? Divida os pedidos CANCELADOS por todos os pedidos do canal no período, inclusive PENDENTES e CONCLUIDOS; mostre canais com pedidos e arredonde para duas casas.
SELECT canal_venda,
       COUNT(*) AS total_pedidos,
       COUNT(*) FILTER (WHERE status = 'CANCELADO') AS cancelados,
       ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'CANCELADO') / COUNT(*), 2) AS taxa_cancelamento_pct
FROM dataset.pedidos
WHERE data_pedido >= DATE '2025-01-01'
  AND data_pedido < DATE '2026-01-01'
GROUP BY canal_venda
ORDER BY canal_venda;
