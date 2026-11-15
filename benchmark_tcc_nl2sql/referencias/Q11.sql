-- Q11 — Qual foi o faturamento de pedidos CONCLUIDOS em 2025 por canal de venda? Mostre os canais com vendas, em ordem alfabética.
SELECT canal_venda,
       SUM(valor_total) AS faturamento
FROM dataset.pedidos
WHERE status = 'CONCLUIDO'
  AND data_pedido >= DATE '2025-01-01'
  AND data_pedido < DATE '2026-01-01'
GROUP BY canal_venda
ORDER BY canal_venda;
