-- Q28 — Qual foi o vendedor com maior faturamento de pedidos CONCLUIDOS em 2025 em cada região de atuação? Considere vendedores ativos e inativos, somente os que tiveram vendas; em empate de faturamento, escolha o menor ID do vendedor. Exiba região, ID, nome e faturamento, ordenados por região.
WITH receita_vendedor AS (
    SELECT v.regiao, v.id AS vendedor_id, v.nome AS vendedor,
           SUM(p.valor_total) AS faturamento
    FROM dataset.vendedores v
    JOIN dataset.pedidos p ON p.vendedor_id = v.id
    WHERE p.status = 'CONCLUIDO'
      AND p.data_pedido >= DATE '2025-01-01'
      AND p.data_pedido < DATE '2026-01-01'
    GROUP BY v.regiao, v.id, v.nome
), ranqueados AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY regiao
        ORDER BY faturamento DESC, vendedor_id ASC
    ) AS posicao
    FROM receita_vendedor
)
SELECT regiao, vendedor_id, vendedor, faturamento
FROM ranqueados
WHERE posicao = 1
ORDER BY regiao;
