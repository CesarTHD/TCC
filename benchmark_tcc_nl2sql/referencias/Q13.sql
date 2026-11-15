-- Q13 — Qual foi o faturamento por categoria de produto em pedidos CONCLUIDOS em 2025? Considere o valor líquido dos itens e mostre somente categorias com vendas, ordenadas por nome.
SELECT c.id AS categoria_id,
       c.nome AS categoria,
       SUM(i.valor_total_item) AS faturamento
FROM dataset.categorias c
JOIN dataset.produtos pr ON pr.categoria_id = c.id
JOIN dataset.itens_pedido i ON i.produto_id = pr.id
JOIN dataset.pedidos p ON p.id = i.pedido_id
WHERE p.status = 'CONCLUIDO'
  AND p.data_pedido >= DATE '2025-01-01'
  AND p.data_pedido < DATE '2026-01-01'
GROUP BY c.id, c.nome
ORDER BY c.nome, c.id;
