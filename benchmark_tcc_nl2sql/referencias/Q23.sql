-- Q23 — Para cada mês de 2025, inclusive meses sem vendas, qual foi o faturamento de pedidos CONCLUIDOS e a variação absoluta em reais em relação ao mês anterior? Para janeiro, a variação deve ser NULL. Ordene cronologicamente.
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
