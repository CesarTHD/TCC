-- Q21 — Quantos clientes tiveram sua primeira compra CONCLUIDA da história em 2025, por canal dessa primeira compra? Se houver duas compras na mesma data, considere primeiro o pedido de menor ID. Mostre os canais com clientes adquiridos, em ordem alfabética.
WITH primeiras AS (
    SELECT p.cliente_id,
           p.canal_venda,
           p.data_pedido,
           ROW_NUMBER() OVER (
               PARTITION BY p.cliente_id
               ORDER BY p.data_pedido, p.id
           ) AS posicao
    FROM dataset.pedidos p
    WHERE p.status = 'CONCLUIDO'
)
SELECT canal_venda AS canal_aquisicao,
       COUNT(*) AS clientes_adquiridos
FROM primeiras
WHERE posicao = 1
  AND data_pedido >= DATE '2025-01-01'
  AND data_pedido < DATE '2026-01-01'
GROUP BY canal_venda
ORDER BY canal_venda;
