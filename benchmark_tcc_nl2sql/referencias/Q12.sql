-- Q12 — Quais foram os dez clientes que mais geraram faturamento em pedidos CONCLUIDOS em 2025? Exiba ID, nome e faturamento, ordenando por faturamento decrescente e ID crescente em empates.
SELECT c.id AS cliente_id,
       c.nome AS cliente,
       SUM(p.valor_total) AS faturamento
FROM dataset.clientes c
JOIN dataset.pedidos p ON p.cliente_id = c.id
WHERE p.status = 'CONCLUIDO'
  AND p.data_pedido >= DATE '2025-01-01'
  AND p.data_pedido < DATE '2026-01-01'
GROUP BY c.id, c.nome
ORDER BY faturamento DESC, c.id ASC
LIMIT 10;
