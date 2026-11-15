-- =============================================================================
-- TCC NL2SQL — Validação do dataset
--
-- Parte A: estatísticas descritivas (informativas).
-- Parte B: verificações de integridade. Cada verificação conta ocorrências de
--          erro e DEVE resultar em 0. Se alguma for > 0, o script termina com
--          erro (exit code != 0 no psql com ON_ERROR_STOP).
--
-- Executar como a role administrativa (usa uma tabela temporária):
--   psql -U tcc_admin -d tcc_nl2sql -f database/validation.sql
-- =============================================================================

\set ON_ERROR_STOP on
\pset footer off
SET datestyle = 'ISO, YMD';

-- ============================ PARTE A ========================================

\echo '\n== A1. Registros por tabela'
SELECT 'categorias' AS tabela, count(*) AS registros FROM dataset.categorias
UNION ALL SELECT 'produtos', count(*) FROM dataset.produtos
UNION ALL SELECT 'vendedores', count(*) FROM dataset.vendedores
UNION ALL SELECT 'clientes', count(*) FROM dataset.clientes
UNION ALL SELECT 'pedidos', count(*) FROM dataset.pedidos
UNION ALL SELECT 'itens_pedido', count(*) FROM dataset.itens_pedido;

\echo '\n== A2. Intervalo de datas'
SELECT 'pedidos.data_pedido' AS coluna, min(data_pedido) AS minimo, max(data_pedido) AS maximo FROM dataset.pedidos
UNION ALL SELECT 'clientes.data_cadastro', min(data_cadastro), max(data_cadastro) FROM dataset.clientes
UNION ALL SELECT 'clientes.data_nascimento', min(data_nascimento), max(data_nascimento) FROM dataset.clientes
UNION ALL SELECT 'produtos.data_cadastro', min(data_cadastro), max(data_cadastro) FROM dataset.produtos
UNION ALL SELECT 'vendedores.data_admissao', min(data_admissao), max(data_admissao) FROM dataset.vendedores
UNION ALL SELECT 'vendedores.data_desligamento', min(data_desligamento), max(data_desligamento) FROM dataset.vendedores;

\echo '\n== A3. Pedidos por ano'
SELECT extract(year FROM data_pedido)::int AS ano, count(*) AS pedidos,
       count(*) FILTER (WHERE status = 'CONCLUIDO') AS concluidos,
       sum(valor_total) FILTER (WHERE status = 'CONCLUIDO') AS faturamento
FROM dataset.pedidos GROUP BY 1 ORDER BY 1;

\echo '\n== A4. Pedidos por status'
SELECT status, count(*) AS pedidos, round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS pct
FROM dataset.pedidos GROUP BY status ORDER BY pedidos DESC;

\echo '\n== A5. Pedidos por canal'
SELECT canal_venda, count(*) AS pedidos, round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS pct
FROM dataset.pedidos GROUP BY canal_venda ORDER BY pedidos DESC;

\echo '\n== A6. Clientes por UF'
SELECT uf, count(*) AS clientes, round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS pct
FROM dataset.clientes GROUP BY uf ORDER BY clientes DESC, uf;

\echo '\n== A7. Clientes por quantidade de pedidos (todos os status)'
SELECT CASE WHEN n = 0 THEN '0' WHEN n = 1 THEN '1' WHEN n <= 5 THEN '2-5'
            WHEN n <= 20 THEN '6-20' ELSE '21+' END AS faixa_pedidos,
       count(*) AS clientes
FROM (SELECT c.id, count(p.id) AS n FROM dataset.clientes c
      LEFT JOIN dataset.pedidos p ON p.cliente_id = c.id GROUP BY c.id) t
GROUP BY 1 ORDER BY min(n);

\echo '\n== A8. Pedidos por quantidade de itens'
SELECT itens, count(*) AS pedidos
FROM (SELECT pedido_id, count(*) AS itens FROM dataset.itens_pedido GROUP BY pedido_id) t
GROUP BY itens ORDER BY itens;

\echo '\n== A9. Produtos ativos x inativos'
SELECT ativo, count(*) AS produtos FROM dataset.produtos GROUP BY ativo ORDER BY ativo DESC;

\echo '\n== A10. Pedidos por mês do ano (sazonalidade, todos os anos)'
SELECT extract(month FROM data_pedido)::int AS mes, count(*) AS pedidos
FROM dataset.pedidos GROUP BY 1 ORDER BY 1;

-- ============================ PARTE B ========================================

CREATE TEMP TABLE validacao (verificacao text, ocorrencias bigint) ON COMMIT PRESERVE ROWS;
TRUNCATE validacao;

INSERT INTO validacao
-- Integridade referencial (redundante com as FKs, mas explícito)
SELECT 'pedidos sem cliente', count(*) FROM dataset.pedidos p
    LEFT JOIN dataset.clientes c ON c.id = p.cliente_id WHERE c.id IS NULL
UNION ALL SELECT 'pedidos sem vendedor', count(*) FROM dataset.pedidos p
    LEFT JOIN dataset.vendedores v ON v.id = p.vendedor_id WHERE v.id IS NULL
UNION ALL SELECT 'itens sem pedido', count(*) FROM dataset.itens_pedido i
    LEFT JOIN dataset.pedidos p ON p.id = i.pedido_id WHERE p.id IS NULL
UNION ALL SELECT 'itens sem produto', count(*) FROM dataset.itens_pedido i
    LEFT JOIN dataset.produtos pr ON pr.id = i.produto_id WHERE pr.id IS NULL
UNION ALL SELECT 'produtos sem categoria', count(*) FROM dataset.produtos pr
    LEFT JOIN dataset.categorias ca ON ca.id = pr.categoria_id WHERE ca.id IS NULL
UNION ALL SELECT 'pedidos sem itens', count(*) FROM dataset.pedidos p
    WHERE NOT EXISTS (SELECT 1 FROM dataset.itens_pedido i WHERE i.pedido_id = p.id)
-- Regras numéricas
UNION ALL SELECT 'quantidade <= 0', count(*) FROM dataset.itens_pedido WHERE quantidade <= 0
UNION ALL SELECT 'preço de produto <= 0', count(*) FROM dataset.produtos WHERE preco <= 0
UNION ALL SELECT 'preço unitário <= 0', count(*) FROM dataset.itens_pedido WHERE preco_unitario <= 0
UNION ALL SELECT 'desconto inválido (< 0 ou > valor bruto)', count(*) FROM dataset.itens_pedido
    WHERE desconto < 0 OR desconto > quantidade * preco_unitario
UNION ALL SELECT 'valor_total_item <> quantidade*preco_unitario-desconto', count(*) FROM dataset.itens_pedido
    WHERE valor_total_item <> quantidade * preco_unitario - desconto
UNION ALL SELECT 'pedidos.valor_total <> soma dos itens', count(*) FROM dataset.pedidos p
    JOIN (SELECT pedido_id, sum(valor_total_item) AS soma FROM dataset.itens_pedido GROUP BY pedido_id) s
      ON s.pedido_id = p.id
    WHERE p.valor_total <> s.soma
UNION ALL SELECT 'valor_total de pedido negativo', count(*) FROM dataset.pedidos WHERE valor_total < 0
-- Coerência temporal
UNION ALL SELECT 'pedido anterior ao cadastro do cliente', count(*) FROM dataset.pedidos p
    JOIN dataset.clientes c ON c.id = p.cliente_id WHERE p.data_pedido < c.data_cadastro
UNION ALL SELECT 'pedido anterior à admissão do vendedor', count(*) FROM dataset.pedidos p
    JOIN dataset.vendedores v ON v.id = p.vendedor_id WHERE p.data_pedido < v.data_admissao
UNION ALL SELECT 'pedido posterior ao desligamento do vendedor', count(*) FROM dataset.pedidos p
    JOIN dataset.vendedores v ON v.id = p.vendedor_id WHERE p.data_pedido > v.data_desligamento
UNION ALL SELECT 'venda anterior ao cadastro do produto', count(*) FROM dataset.itens_pedido i
    JOIN dataset.pedidos p ON p.id = i.pedido_id
    JOIN dataset.produtos pr ON pr.id = i.produto_id WHERE p.data_pedido < pr.data_cadastro
UNION ALL SELECT 'pedido fora de 2023-01-01..2026-09-30', count(*) FROM dataset.pedidos
    WHERE data_pedido < DATE '2023-01-01' OR data_pedido > DATE '2026-09-30'
UNION ALL SELECT 'registros com data futura (> 2026-09-30)',
    (SELECT count(*) FROM dataset.clientes WHERE data_cadastro > DATE '2026-09-30' OR data_nascimento > DATE '2026-09-30')
  + (SELECT count(*) FROM dataset.produtos WHERE data_cadastro > DATE '2026-09-30')
  + (SELECT count(*) FROM dataset.vendedores WHERE data_admissao > DATE '2026-09-30' OR data_desligamento > DATE '2026-09-30')
  + (SELECT count(*) FROM dataset.pedidos WHERE data_pedido > DATE '2026-09-30')
UNION ALL SELECT 'cliente menor de 18 anos no cadastro', count(*) FROM dataset.clientes
    WHERE data_nascimento > data_cadastro - INTERVAL '18 years'
UNION ALL SELECT 'vendedor com desligamento <= admissão', count(*) FROM dataset.vendedores
    WHERE data_desligamento <= data_admissao
-- Valores categóricos
UNION ALL SELECT 'pedidos.status inválido', count(*) FROM dataset.pedidos
    WHERE status NOT IN ('CONCLUIDO', 'CANCELADO', 'PENDENTE')
UNION ALL SELECT 'pedidos.canal_venda inválido', count(*) FROM dataset.pedidos
    WHERE canal_venda NOT IN ('SITE', 'LOJA', 'APP', 'TELEFONE')
UNION ALL SELECT 'clientes.status/segmento inválido', count(*) FROM dataset.clientes
    WHERE status NOT IN ('ATIVO', 'INATIVO') OR segmento NOT IN ('PADRAO', 'PREMIUM')
UNION ALL SELECT 'vendedores.status incoerente com data_desligamento', count(*) FROM dataset.vendedores
    WHERE (status = 'INATIVO') <> (data_desligamento IS NOT NULL) OR status NOT IN ('ATIVO', 'INATIVO')
UNION ALL SELECT 'vendedores.regiao inválida', count(*) FROM dataset.vendedores
    WHERE regiao NOT IN ('NORTE', 'NORDESTE', 'CENTRO-OESTE', 'SUDESTE', 'SUL')
-- Dados pessoais fictícios
UNION ALL SELECT 'e-mail fora do domínio reservado example.com', count(*) FROM (
    SELECT email FROM dataset.clientes UNION ALL SELECT email FROM dataset.vendedores) e
    WHERE email !~ '^[a-z0-9.]+@([a-z]+\.)?example\.com$';

\echo '\n== B. Verificações de integridade (ocorrencias deve ser 0)'
SELECT verificacao, ocorrencias, CASE WHEN ocorrencias = 0 THEN 'OK' ELSE 'FALHA' END AS resultado
FROM validacao;

DO $$
DECLARE
    falhas int;
BEGIN
    SELECT count(*) INTO falhas FROM validacao WHERE ocorrencias <> 0;
    IF falhas > 0 THEN
        RAISE EXCEPTION 'VALIDAÇÃO FALHOU: % verificação(ões) com ocorrências', falhas;
    END IF;
    RAISE NOTICE 'VALIDAÇÃO OK: todas as % verificações retornaram 0 ocorrências',
        (SELECT count(*) FROM validacao);
END $$;
