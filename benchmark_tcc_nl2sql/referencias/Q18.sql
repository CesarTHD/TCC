-- Q18 — Qual foi o faturamento mensal de pedidos CONCLUIDOS em 2025? Exiba apenas meses com vendas, em ordem cronológica.
SELECT DATE_TRUNC('month', data_pedido)::date AS mes,
       SUM(valor_total) AS faturamento
FROM dataset.pedidos
WHERE status = 'CONCLUIDO'
  AND data_pedido >= DATE '2025-01-01'
  AND data_pedido < DATE '2026-01-01'
GROUP BY DATE_TRUNC('month', data_pedido)::date
ORDER BY mes;
