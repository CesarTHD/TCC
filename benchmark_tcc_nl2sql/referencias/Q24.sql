-- Q24 — Quais foram os três produtos de maior faturamento líquido em cada categoria em 2025, considerando somente pedidos CONCLUIDOS? Mostre categoria, produto, receita e posição; em empate de receita, use o menor ID do produto como desempate e retorne no máximo três por categoria.
WITH receita_produto AS (
    SELECT c.id AS categoria_id,
           c.nome AS categoria,
           pr.id AS produto_id,
           pr.nome AS produto,
           SUM(i.valor_total_item) AS receita
    FROM dataset.categorias c
    JOIN dataset.produtos pr ON pr.categoria_id = c.id
    JOIN dataset.itens_pedido i ON i.produto_id = pr.id
    JOIN dataset.pedidos p ON p.id = i.pedido_id
    WHERE p.status = 'CONCLUIDO'
      AND p.data_pedido >= DATE '2025-01-01'
      AND p.data_pedido < DATE '2026-01-01'
    GROUP BY c.id, c.nome, pr.id, pr.nome
), ranqueados AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY categoria_id
        ORDER BY receita DESC, produto_id ASC
    ) AS posicao
    FROM receita_produto
)
SELECT categoria_id, categoria, produto_id, produto, receita, posicao
FROM ranqueados
WHERE posicao <= 3
ORDER BY categoria_id, posicao;
