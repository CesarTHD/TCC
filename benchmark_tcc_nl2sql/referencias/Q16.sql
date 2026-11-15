-- Q16 — Qual foi o ticket médio dos pedidos CONCLUIDOS em 2025 por UF do cliente? Exiba UF, número de pedidos e ticket médio em reais, incluindo somente UFs com vendas e ordenando pela UF.
SELECT c.uf,
       COUNT(p.id) AS total_pedidos,
       ROUND(AVG(p.valor_total), 2) AS ticket_medio
FROM dataset.clientes c
JOIN dataset.pedidos p ON p.cliente_id = c.id
WHERE p.status = 'CONCLUIDO'
  AND p.data_pedido >= DATE '2025-01-01'
  AND p.data_pedido < DATE '2026-01-01'
GROUP BY c.uf
ORDER BY c.uf;
