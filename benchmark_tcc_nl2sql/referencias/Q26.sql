-- Q26 — Para cada coorte mensal de clientes cuja primeira compra CONCLUIDA ocorreu em 2024, qual foi a retenção no mês M3? Defina M3 como o terceiro mês-calendário após o mês da primeira compra e retenção como ao menos um pedido CONCLUIDO nesse mês. Mostre coorte, clientes, retidos e percentual com duas casas, em ordem cronológica.
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
