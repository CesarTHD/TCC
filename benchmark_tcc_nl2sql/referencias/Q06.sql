-- Q06 — Qual foi o ticket médio dos pedidos CONCLUIDOS em 2025, em reais por pedido?
SELECT ROUND(AVG(valor_total), 2) AS ticket_medio_2025
FROM dataset.pedidos
WHERE status = 'CONCLUIDO'
  AND data_pedido >= DATE '2025-01-01'
  AND data_pedido < DATE '2026-01-01';
