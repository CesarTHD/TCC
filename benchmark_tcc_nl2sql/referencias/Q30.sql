-- Q30 — Entre produtos atualmente ativos que tiveram unidades vendidas em pedidos CONCLUIDOS em 2025, quais são os dez com maior diferença absoluta, em reais, entre o preço de tabela atual e o preço unitário médio efetivamente recebido em 2025 (receita líquida dividida por unidades)? Exiba ID, nome, preços, diferença absoluta; desempate por ID crescente e arredonde o preço médio e a diferença para duas casas.
WITH vendas_produto AS (
    SELECT pr.id AS produto_id,
           pr.nome AS produto,
           pr.preco AS preco_atual,
           SUM(i.valor_total_item) AS receita_liquida,
           SUM(i.quantidade) AS unidades
    FROM dataset.produtos pr
    JOIN dataset.itens_pedido i ON i.produto_id = pr.id
    JOIN dataset.pedidos p ON p.id = i.pedido_id
    WHERE pr.ativo = TRUE
      AND p.status = 'CONCLUIDO'
      AND p.data_pedido >= DATE '2025-01-01'
      AND p.data_pedido < DATE '2026-01-01'
    GROUP BY pr.id, pr.nome, pr.preco
), precos AS (
    SELECT produto_id, produto, preco_atual,
           ROUND(receita_liquida / NULLIF(unidades, 0), 2) AS preco_medio_realizado,
           ROUND(ABS(preco_atual - receita_liquida / NULLIF(unidades, 0)), 2) AS diferenca_absoluta
    FROM vendas_produto
)
SELECT produto_id, produto, preco_atual, preco_medio_realizado, diferenca_absoluta
FROM precos
ORDER BY diferenca_absoluta DESC, produto_id ASC
LIMIT 10;
