-- Q29 — Quais foram os dez pares de produtos distintos que mais apareceram juntos no mesmo pedido CONCLUIDO em 2025? Conte pedidos que contêm ambos os produtos, não unidades; exiba IDs, nomes e quantidade de pedidos, com desempate por IDs crescentes.
SELECT i1.produto_id AS produto_1_id,
       pr1.nome AS produto_1,
       i2.produto_id AS produto_2_id,
       pr2.nome AS produto_2,
       COUNT(*) AS pedidos_em_conjunto
FROM dataset.pedidos p
JOIN dataset.itens_pedido i1 ON i1.pedido_id = p.id
JOIN dataset.itens_pedido i2 ON i2.pedido_id = p.id
    AND i1.produto_id < i2.produto_id
JOIN dataset.produtos pr1 ON pr1.id = i1.produto_id
JOIN dataset.produtos pr2 ON pr2.id = i2.produto_id
WHERE p.status = 'CONCLUIDO'
  AND p.data_pedido >= DATE '2025-01-01'
  AND p.data_pedido < DATE '2026-01-01'
GROUP BY i1.produto_id, pr1.nome, i2.produto_id, pr2.nome
ORDER BY pedidos_em_conjunto DESC, produto_1_id ASC, produto_2_id ASC
LIMIT 10;
