-- Q05 — Qual foi o faturamento total dos pedidos CONCLUIDOS em 2025, em reais?
SELECT COALESCE(SUM(valor_total), 0) AS faturamento_2025
FROM dataset.pedidos
WHERE status = 'CONCLUIDO'
  AND data_pedido >= DATE '2025-01-01'
  AND data_pedido < DATE '2026-01-01';
