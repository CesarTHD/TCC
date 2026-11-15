-- =============================================================================
-- TCC NL2SQL — Checksums do conteúdo das tabelas
--
-- MD5 da representação textual de todas as linhas de cada tabela, ordenadas
-- por id. Dois bancos com os mesmos valores produzem os mesmos MD5, portanto
-- este script é usado para verificar a reprodutibilidade do seed.
-- Valores de referência: docs/dataset_statistics.md
-- =============================================================================

SET datestyle = 'ISO, YMD';

SELECT 'categorias' AS tabela, count(*) AS linhas, md5(string_agg(t::text, E'\n' ORDER BY t.id)) AS md5 FROM dataset.categorias t
UNION ALL
SELECT 'produtos', count(*), md5(string_agg(t::text, E'\n' ORDER BY t.id)) FROM dataset.produtos t
UNION ALL
SELECT 'vendedores', count(*), md5(string_agg(t::text, E'\n' ORDER BY t.id)) FROM dataset.vendedores t
UNION ALL
SELECT 'clientes', count(*), md5(string_agg(t::text, E'\n' ORDER BY t.id)) FROM dataset.clientes t
UNION ALL
SELECT 'pedidos', count(*), md5(string_agg(t::text, E'\n' ORDER BY t.id)) FROM dataset.pedidos t
UNION ALL
SELECT 'itens_pedido', count(*), md5(string_agg(t::text, E'\n' ORDER BY t.id)) FROM dataset.itens_pedido t;
