-- Q22 — Qual foi a receita média por cliente nos 12 meses após a primeira compra CONCLUIDA, agrupada pelo canal dessa primeira compra? Inclua a primeira compra, exclua CANCELADOS e PENDENTES, considere apenas clientes cuja primeira compra ocorreu até 30/09/2025, e use janela de 12 meses com início inclusivo e fim exclusivo. Em empate de data, a primeira compra é a de menor ID. Mostre canal, quantidade de clientes e média em reais, ordenados pelo canal.
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
