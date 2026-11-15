# Benchmark NL2SQL — 30 perguntas e SQLs de referência

**Status:** rascunho para revisão independente e execução no PostgreSQL.
**Banco:** PostgreSQL 16, schema `dataset`. **Data fixa:** 2026-09-30.

**Convenções:** pedidos concluídos para faturamento; datas finais exclusivas; `valor_total` no cabeçalho de pedidos e `valor_total_item` para faturamento por produto/categoria; preço de tabela atual não representa preço histórico.

**Importante:** os SQLs foram escritos a partir do catálogo semântico fornecido, mas não foram executados contra o banco real. Verifique-os antes de congelar o benchmark. Não há resultados esperados numéricos inventados.

## Índice

| ID | Nível | Pergunta |
|---|---|---|
| Q01 | simples | Quantos clientes existem cadastrados, independentemente do status? |
| Q02 | simples | Quantos produtos estão ativos no catálogo? |
| Q03 | simples | Quantos vendedores estão atualmente com status ATIVO? |
| Q04 | simples | Quantos pedidos com status CANCELADO foram registrados durante o ano de 2025? |
| Q05 | simples | Qual foi o faturamento total dos pedidos CONCLUIDOS em 2025, em reais? |
| Q06 | simples | Qual foi o ticket médio dos pedidos CONCLUIDOS em 2025, em reais por pedido? |
| Q07 | simples | Quantos pedidos CONCLUIDOS foram realizados pelo canal SITE de 1º de janeiro a 30 de setembro de 2026, inclusive? |
| Q08 | simples | Quantos clientes do segmento PREMIUM, com status ATIVO, estão cadastrados na UF DF? |
| Q09 | simples | Qual é o maior preço de tabela atual entre os produtos ativos? |
| Q10 | simples | Quantas cidades distintas possuem clientes cadastrados na UF SP? |
| Q11 | intermediaria | Qual foi o faturamento de pedidos CONCLUIDOS em 2025 por canal de venda? Mostre os canais com vendas, em ordem alfabética. |
| Q12 | intermediaria | Quais foram os dez clientes que mais geraram faturamento em pedidos CONCLUIDOS em 2025? Exiba ID, nome e faturamento, ordenando por faturamento decrescente e ID crescente em empates. |
| Q13 | intermediaria | Qual foi o faturamento por categoria de produto em pedidos CONCLUIDOS em 2025? Considere o valor líquido dos itens e mostre somente categorias com vendas, ordenadas por nome. |
| Q14 | intermediaria | Quais foram os dez produtos com maior quantidade de unidades vendidas em pedidos CONCLUIDOS em 2025? Exiba ID, nome e unidades, com desempate por ID crescente. |
| Q15 | intermediaria | Qual foi o faturamento de cada vendedor que realizou pelo menos um pedido CONCLUIDO em 2025, incluindo vendedores hoje inativos? Ordene por faturamento decrescente e ID crescente. |
| Q16 | intermediaria | Qual foi o ticket médio dos pedidos CONCLUIDOS em 2025 por UF do cliente? Exiba UF, número de pedidos e ticket médio em reais, incluindo somente UFs com vendas e ordenando pela UF. |
| Q17 | intermediaria | Quantos clientes cadastrados nunca realizaram um pedido CONCLUIDO até 30 de setembro de 2026, inclusive? |
| Q18 | intermediaria | Qual foi o faturamento mensal de pedidos CONCLUIDOS em 2025? Exiba apenas meses com vendas, em ordem cronológica. |
| Q19 | intermediaria | Quantos pedidos CONCLUIDOS foram realizados em 2025 por clientes de cada segmento de fidelidade? Mostre apenas segmentos com pedidos, ordenados pelo nome do segmento. |
| Q20 | intermediaria | Qual foi a taxa percentual de cancelamento por canal de venda em 2025? Divida os pedidos CANCELADOS por todos os pedidos do canal no período, inclusive PENDENTES e CONCLUIDOS; mostre canais com pedidos e arredonde para duas casas. |
| Q21 | complexa | Quantos clientes tiveram sua primeira compra CONCLUIDA da história em 2025, por canal dessa primeira compra? Se houver duas compras na mesma data, considere primeiro o pedido de menor ID. Mostre os canais com clientes adquiridos, em ordem alfabética. |
| Q22 | complexa | Qual foi a receita média por cliente nos 12 meses após a primeira compra CONCLUIDA, agrupada pelo canal dessa primeira compra? Inclua a primeira compra, exclua CANCELADOS e PENDENTES, considere apenas clientes cuja primeira compra ocorreu até 30/09/2025, e use janela de 12 meses com início inclusivo e fim exclusivo. Em empate de data, a primeira compra é a de menor ID. Mostre canal, quantidade de clientes e média em reais, ordenados pelo canal. |
| Q23 | complexa | Para cada mês de 2025, inclusive meses sem vendas, qual foi o faturamento de pedidos CONCLUIDOS e a variação absoluta em reais em relação ao mês anterior? Para janeiro, a variação deve ser NULL. Ordene cronologicamente. |
| Q24 | complexa | Quais foram os três produtos de maior faturamento líquido em cada categoria em 2025, considerando somente pedidos CONCLUIDOS? Mostre categoria, produto, receita e posição; em empate de receita, use o menor ID do produto como desempate e retorne no máximo três por categoria. |
| Q25 | complexa | Quantos clientes fizeram pelo menos uma compra CONCLUIDA em 2024, mas nenhuma compra CONCLUIDA em 2025? Compras em outros anos não impedem a inclusão. |
| Q26 | complexa | Para cada coorte mensal de clientes cuja primeira compra CONCLUIDA ocorreu em 2024, qual foi a retenção no mês M3? Defina M3 como o terceiro mês-calendário após o mês da primeira compra e retenção como ao menos um pedido CONCLUIDO nesse mês. Mostre coorte, clientes, retidos e percentual com duas casas, em ordem cronológica. |
| Q27 | complexa | Qual foi a participação percentual de cada canal no faturamento de pedidos CONCLUIDOS de 2025 e a participação acumulada? Ordene os canais por faturamento decrescente e, em empate, por nome crescente. Arredonde os percentuais para duas casas. |
| Q28 | complexa | Qual foi o vendedor com maior faturamento de pedidos CONCLUIDOS em 2025 em cada região de atuação? Considere vendedores ativos e inativos, somente os que tiveram vendas; em empate de faturamento, escolha o menor ID do vendedor. Exiba região, ID, nome e faturamento, ordenados por região. |
| Q29 | complexa | Quais foram os dez pares de produtos distintos que mais apareceram juntos no mesmo pedido CONCLUIDO em 2025? Conte pedidos que contêm ambos os produtos, não unidades; exiba IDs, nomes e quantidade de pedidos, com desempate por IDs crescentes. |
| Q30 | complexa | Entre produtos atualmente ativos que tiveram unidades vendidas em pedidos CONCLUIDOS em 2025, quais são os dez com maior diferença absoluta, em reais, entre o preço de tabela atual e o preço unitário médio efetivamente recebido em 2025 (receita líquida dividida por unidades)? Exiba ID, nome, preços, diferença absoluta; desempate por ID crescente e arredonde o preço médio e a diferença para duas casas. |

## Q01 — Simples

Quantos clientes existem cadastrados, independentemente do status?

```sql
SELECT COUNT(*) AS total_clientes
FROM dataset.clientes;
```

## Q02 — Simples

Quantos produtos estão ativos no catálogo?

```sql
SELECT COUNT(*) AS produtos_ativos
FROM dataset.produtos
WHERE ativo = TRUE;
```

## Q03 — Simples

Quantos vendedores estão atualmente com status ATIVO?

```sql
SELECT COUNT(*) AS vendedores_ativos
FROM dataset.vendedores
WHERE status = 'ATIVO';
```

## Q04 — Simples

Quantos pedidos com status CANCELADO foram registrados durante o ano de 2025?

```sql
SELECT COUNT(*) AS pedidos_cancelados
FROM dataset.pedidos
WHERE status = 'CANCELADO'
  AND data_pedido >= DATE '2025-01-01'
  AND data_pedido < DATE '2026-01-01';
```

## Q05 — Simples

Qual foi o faturamento total dos pedidos CONCLUIDOS em 2025, em reais?

```sql
SELECT COALESCE(SUM(valor_total), 0) AS faturamento_2025
FROM dataset.pedidos
WHERE status = 'CONCLUIDO'
  AND data_pedido >= DATE '2025-01-01'
  AND data_pedido < DATE '2026-01-01';
```

## Q06 — Simples

Qual foi o ticket médio dos pedidos CONCLUIDOS em 2025, em reais por pedido?

```sql
SELECT ROUND(AVG(valor_total), 2) AS ticket_medio_2025
FROM dataset.pedidos
WHERE status = 'CONCLUIDO'
  AND data_pedido >= DATE '2025-01-01'
  AND data_pedido < DATE '2026-01-01';
```

## Q07 — Simples

Quantos pedidos CONCLUIDOS foram realizados pelo canal SITE de 1º de janeiro a 30 de setembro de 2026, inclusive?

```sql
SELECT COUNT(*) AS pedidos_site_2026
FROM dataset.pedidos
WHERE status = 'CONCLUIDO'
  AND canal_venda = 'SITE'
  AND data_pedido >= DATE '2026-01-01'
  AND data_pedido < DATE '2026-10-01';
```

## Q08 — Simples

Quantos clientes do segmento PREMIUM, com status ATIVO, estão cadastrados na UF DF?

```sql
SELECT COUNT(*) AS clientes_premium_ativos_df
FROM dataset.clientes
WHERE segmento = 'PREMIUM'
  AND status = 'ATIVO'
  AND uf = 'DF';
```

## Q09 — Simples

Qual é o maior preço de tabela atual entre os produtos ativos?

```sql
SELECT MAX(preco) AS maior_preco_atual
FROM dataset.produtos
WHERE ativo = TRUE;
```

## Q10 — Simples

Quantas cidades distintas possuem clientes cadastrados na UF SP?

```sql
SELECT COUNT(DISTINCT cidade) AS cidades_distintas_sp
FROM dataset.clientes
WHERE uf = 'SP';
```

## Q11 — Intermediaria

Qual foi o faturamento de pedidos CONCLUIDOS em 2025 por canal de venda? Mostre os canais com vendas, em ordem alfabética.

```sql
SELECT canal_venda,
       SUM(valor_total) AS faturamento
FROM dataset.pedidos
WHERE status = 'CONCLUIDO'
  AND data_pedido >= DATE '2025-01-01'
  AND data_pedido < DATE '2026-01-01'
GROUP BY canal_venda
ORDER BY canal_venda;
```

## Q12 — Intermediaria

Quais foram os dez clientes que mais geraram faturamento em pedidos CONCLUIDOS em 2025? Exiba ID, nome e faturamento, ordenando por faturamento decrescente e ID crescente em empates.

```sql
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
```

## Q13 — Intermediaria

Qual foi o faturamento por categoria de produto em pedidos CONCLUIDOS em 2025? Considere o valor líquido dos itens e mostre somente categorias com vendas, ordenadas por nome.

```sql
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
```

## Q14 — Intermediaria

Quais foram os dez produtos com maior quantidade de unidades vendidas em pedidos CONCLUIDOS em 2025? Exiba ID, nome e unidades, com desempate por ID crescente.

```sql
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
```

## Q15 — Intermediaria

Qual foi o faturamento de cada vendedor que realizou pelo menos um pedido CONCLUIDO em 2025, incluindo vendedores hoje inativos? Ordene por faturamento decrescente e ID crescente.

```sql
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
```

## Q16 — Intermediaria

Qual foi o ticket médio dos pedidos CONCLUIDOS em 2025 por UF do cliente? Exiba UF, número de pedidos e ticket médio em reais, incluindo somente UFs com vendas e ordenando pela UF.

```sql
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
```

## Q17 — Intermediaria

Quantos clientes cadastrados nunca realizaram um pedido CONCLUIDO até 30 de setembro de 2026, inclusive?

```sql
SELECT COUNT(*) AS clientes_sem_compra_concluida
FROM dataset.clientes c
WHERE NOT EXISTS (
    SELECT 1
    FROM dataset.pedidos p
    WHERE p.cliente_id = c.id
      AND p.status = 'CONCLUIDO'
      AND p.data_pedido < DATE '2026-10-01'
);
```

## Q18 — Intermediaria

Qual foi o faturamento mensal de pedidos CONCLUIDOS em 2025? Exiba apenas meses com vendas, em ordem cronológica.

```sql
SELECT DATE_TRUNC('month', data_pedido)::date AS mes,
       SUM(valor_total) AS faturamento
FROM dataset.pedidos
WHERE status = 'CONCLUIDO'
  AND data_pedido >= DATE '2025-01-01'
  AND data_pedido < DATE '2026-01-01'
GROUP BY DATE_TRUNC('month', data_pedido)::date
ORDER BY mes;
```

## Q19 — Intermediaria

Quantos pedidos CONCLUIDOS foram realizados em 2025 por clientes de cada segmento de fidelidade? Mostre apenas segmentos com pedidos, ordenados pelo nome do segmento.

```sql
SELECT c.segmento,
       COUNT(p.id) AS total_pedidos
FROM dataset.clientes c
JOIN dataset.pedidos p ON p.cliente_id = c.id
WHERE p.status = 'CONCLUIDO'
  AND p.data_pedido >= DATE '2025-01-01'
  AND p.data_pedido < DATE '2026-01-01'
GROUP BY c.segmento
ORDER BY c.segmento;
```

## Q20 — Intermediaria

Qual foi a taxa percentual de cancelamento por canal de venda em 2025? Divida os pedidos CANCELADOS por todos os pedidos do canal no período, inclusive PENDENTES e CONCLUIDOS; mostre canais com pedidos e arredonde para duas casas.

```sql
SELECT canal_venda,
       COUNT(*) AS total_pedidos,
       COUNT(*) FILTER (WHERE status = 'CANCELADO') AS cancelados,
       ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'CANCELADO') / COUNT(*), 2) AS taxa_cancelamento_pct
FROM dataset.pedidos
WHERE data_pedido >= DATE '2025-01-01'
  AND data_pedido < DATE '2026-01-01'
GROUP BY canal_venda
ORDER BY canal_venda;
```

## Q21 — Complexa

Quantos clientes tiveram sua primeira compra CONCLUIDA da história em 2025, por canal dessa primeira compra? Se houver duas compras na mesma data, considere primeiro o pedido de menor ID. Mostre os canais com clientes adquiridos, em ordem alfabética.

```sql
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
```

## Q22 — Complexa

Qual foi a receita média por cliente nos 12 meses após a primeira compra CONCLUIDA, agrupada pelo canal dessa primeira compra? Inclua a primeira compra, exclua CANCELADOS e PENDENTES, considere apenas clientes cuja primeira compra ocorreu até 30/09/2025, e use janela de 12 meses com início inclusivo e fim exclusivo. Em empate de data, a primeira compra é a de menor ID. Mostre canal, quantidade de clientes e média em reais, ordenados pelo canal.

```sql
WITH concluidos AS (
    SELECT id, cliente_id, data_pedido, canal_venda, valor_total
    FROM dataset.pedidos
    WHERE status = 'CONCLUIDO'
), primeira_compra AS (
    SELECT cliente_id,
           data_pedido AS data_primeira_compra,
           canal_venda AS canal_aquisicao,
           ROW_NUMBER() OVER (
               PARTITION BY cliente_id
               ORDER BY data_pedido, id
           ) AS posicao
    FROM concluidos
), receita_cliente AS (
    SELECT pc.cliente_id,
           pc.canal_aquisicao,
           SUM(p.valor_total) AS receita_12_meses
    FROM primeira_compra pc
    JOIN concluidos p ON p.cliente_id = pc.cliente_id
        AND p.data_pedido >= pc.data_primeira_compra
        AND p.data_pedido < pc.data_primeira_compra + INTERVAL '12 months'
    WHERE pc.posicao = 1
      AND pc.data_primeira_compra <= DATE '2025-09-30'
    GROUP BY pc.cliente_id, pc.canal_aquisicao
)
SELECT canal_aquisicao,
       COUNT(*) AS clientes,
       ROUND(AVG(receita_12_meses), 2) AS receita_media_12_meses
FROM receita_cliente
GROUP BY canal_aquisicao
ORDER BY canal_aquisicao;
```

## Q23 — Complexa

Para cada mês de 2025, inclusive meses sem vendas, qual foi o faturamento de pedidos CONCLUIDOS e a variação absoluta em reais em relação ao mês anterior? Para janeiro, a variação deve ser NULL. Ordene cronologicamente.

```sql
WITH meses AS (
    SELECT GENERATE_SERIES(DATE '2025-01-01', DATE '2025-12-01', INTERVAL '1 month')::date AS mes
), receitas AS (
    SELECT DATE_TRUNC('month', data_pedido)::date AS mes,
           SUM(valor_total) AS faturamento
    FROM dataset.pedidos
    WHERE status = 'CONCLUIDO'
      AND data_pedido >= DATE '2025-01-01'
      AND data_pedido < DATE '2026-01-01'
    GROUP BY DATE_TRUNC('month', data_pedido)::date
), serie AS (
    SELECT m.mes, COALESCE(r.faturamento, 0) AS faturamento
    FROM meses m
    LEFT JOIN receitas r ON r.mes = m.mes
)
SELECT mes,
       faturamento,
       faturamento - LAG(faturamento) OVER (ORDER BY mes) AS variacao_absoluta
FROM serie
ORDER BY mes;
```

## Q24 — Complexa

Quais foram os três produtos de maior faturamento líquido em cada categoria em 2025, considerando somente pedidos CONCLUIDOS? Mostre categoria, produto, receita e posição; em empate de receita, use o menor ID do produto como desempate e retorne no máximo três por categoria.

```sql
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
```

## Q25 — Complexa

Quantos clientes fizeram pelo menos uma compra CONCLUIDA em 2024, mas nenhuma compra CONCLUIDA em 2025? Compras em outros anos não impedem a inclusão.

```sql
SELECT COUNT(*) AS clientes_2024_sem_recompra_2025
FROM dataset.clientes c
WHERE EXISTS (
    SELECT 1
    FROM dataset.pedidos p24
    WHERE p24.cliente_id = c.id
      AND p24.status = 'CONCLUIDO'
      AND p24.data_pedido >= DATE '2024-01-01'
      AND p24.data_pedido < DATE '2025-01-01'
)
AND NOT EXISTS (
    SELECT 1
    FROM dataset.pedidos p25
    WHERE p25.cliente_id = c.id
      AND p25.status = 'CONCLUIDO'
      AND p25.data_pedido >= DATE '2025-01-01'
      AND p25.data_pedido < DATE '2026-01-01'
);
```

## Q26 — Complexa

Para cada coorte mensal de clientes cuja primeira compra CONCLUIDA ocorreu em 2024, qual foi a retenção no mês M3? Defina M3 como o terceiro mês-calendário após o mês da primeira compra e retenção como ao menos um pedido CONCLUIDO nesse mês. Mostre coorte, clientes, retidos e percentual com duas casas, em ordem cronológica.

```sql
WITH primeira_compra AS (
    SELECT cliente_id,
           MIN(data_pedido) AS data_primeira_compra
    FROM dataset.pedidos
    WHERE status = 'CONCLUIDO'
    GROUP BY cliente_id
), coortes AS (
    SELECT cliente_id,
           DATE_TRUNC('month', data_primeira_compra)::date AS mes_coorte
    FROM primeira_compra
    WHERE data_primeira_compra >= DATE '2024-01-01'
      AND data_primeira_compra < DATE '2025-01-01'
), retencao AS (
    SELECT c.cliente_id, c.mes_coorte,
           EXISTS (
               SELECT 1
               FROM dataset.pedidos p
               WHERE p.cliente_id = c.cliente_id
                 AND p.status = 'CONCLUIDO'
                 AND p.data_pedido >= c.mes_coorte + INTERVAL '3 months'
                 AND p.data_pedido < c.mes_coorte + INTERVAL '4 months'
           ) AS retido_m3
    FROM coortes c
)
SELECT mes_coorte,
       COUNT(*) AS clientes_coorte,
       COUNT(*) FILTER (WHERE retido_m3) AS clientes_retidos_m3,
       ROUND(100.0 * COUNT(*) FILTER (WHERE retido_m3) / COUNT(*), 2) AS retencao_m3_pct
FROM retencao
GROUP BY mes_coorte
ORDER BY mes_coorte;
```

## Q27 — Complexa

Qual foi a participação percentual de cada canal no faturamento de pedidos CONCLUIDOS de 2025 e a participação acumulada? Ordene os canais por faturamento decrescente e, em empate, por nome crescente. Arredonde os percentuais para duas casas.

```sql
WITH receita_canal AS (
    SELECT canal_venda,
           SUM(valor_total) AS faturamento
    FROM dataset.pedidos
    WHERE status = 'CONCLUIDO'
      AND data_pedido >= DATE '2025-01-01'
      AND data_pedido < DATE '2026-01-01'
    GROUP BY canal_venda
), participacao AS (
    SELECT canal_venda, faturamento,
           ROUND(100.0 * faturamento / NULLIF(SUM(faturamento) OVER (), 0), 2) AS participacao_pct,
           ROUND(100.0 * SUM(faturamento) OVER (
               ORDER BY faturamento DESC, canal_venda ASC
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
           ) / NULLIF(SUM(faturamento) OVER (), 0), 2) AS participacao_acumulada_pct
    FROM receita_canal
)
SELECT canal_venda, faturamento, participacao_pct, participacao_acumulada_pct
FROM participacao
ORDER BY faturamento DESC, canal_venda ASC;
```

## Q28 — Complexa

Qual foi o vendedor com maior faturamento de pedidos CONCLUIDOS em 2025 em cada região de atuação? Considere vendedores ativos e inativos, somente os que tiveram vendas; em empate de faturamento, escolha o menor ID do vendedor. Exiba região, ID, nome e faturamento, ordenados por região.

```sql
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
```

## Q29 — Complexa

Quais foram os dez pares de produtos distintos que mais apareceram juntos no mesmo pedido CONCLUIDO em 2025? Conte pedidos que contêm ambos os produtos, não unidades; exiba IDs, nomes e quantidade de pedidos, com desempate por IDs crescentes.

```sql
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
```

## Q30 — Complexa

Entre produtos atualmente ativos que tiveram unidades vendidas em pedidos CONCLUIDOS em 2025, quais são os dez com maior diferença absoluta, em reais, entre o preço de tabela atual e o preço unitário médio efetivamente recebido em 2025 (receita líquida dividida por unidades)? Exiba ID, nome, preços, diferença absoluta; desempate por ID crescente e arredonde o preço médio e a diferença para duas casas.

```sql
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
```

## Procedimento para validar o benchmark

1. Revisar a semântica de cada pergunta e o SQL independentemente das saídas dos LLMs.
2. Congelar a versão da base, catálogo, prompts e data de referência.
3. Executar cada SQL no PostgreSQL 16 e salvar resultados no `resultados_esperados.json`.
4. Definir previamente a normalização de resultados: ordenação quando exigida, multiplicidade de linhas, NULLs, datas e precisão numérica.
5. Só então executar A/B/C (cinco repetições por pergunta e configuração).

**Atenção metodológica:** o conjunto foi construído com acesso ao esquema, não com base nos erros ou acertos observados de A/B/C. Após a validação, evite ajustar perguntas em resposta ao desempenho das arquiteturas.
