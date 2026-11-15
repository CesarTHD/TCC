-- Q15 — Qual foi o faturamento de cada vendedor que realizou pelo menos um pedido CONCLUIDO em 2025, incluindo vendedores hoje inativos? Ordene por faturamento decrescente e ID crescente.
SELECT v.id AS vendedor_id,
       v.nome AS vendedor,
       v.status AS status_atual,
       SUM(p.valor_total) AS faturamento
FROM dataset.vendedores v
JOIN dataset.pedidos p ON p.vendedor_id = v.id
WHERE p.status = 'CONCLUIDO'
  AND p.data_pedido >= DATE '2025-01-01'
  AND p.data_pedido < DATE '2026-01-01'
GROUP BY v.id, v.nome, v.status
ORDER BY faturamento DESC, v.id ASC;
