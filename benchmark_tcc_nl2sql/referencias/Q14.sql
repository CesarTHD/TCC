-- Q14 — Quais foram os dez produtos com maior quantidade de unidades vendidas em pedidos CONCLUIDOS em 2025? Exiba ID, nome e unidades, com desempate por ID crescente.
SELECT pr.id AS produto_id,
       pr.nome AS produto,
       SUM(i.quantidade) AS unidades_vendidas
FROM dataset.produtos pr
JOIN dataset.itens_pedido i ON i.produto_id = pr.id
JOIN dataset.pedidos p ON p.id = i.pedido_id
WHERE p.status = 'CONCLUIDO'
  AND p.data_pedido >= DATE '2025-01-01'
  AND p.data_pedido < DATE '2026-01-01'
GROUP BY pr.id, pr.nome
ORDER BY unidades_vendidas DESC, pr.id ASC
LIMIT 10;
