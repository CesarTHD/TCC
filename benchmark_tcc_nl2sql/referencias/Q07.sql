-- Q07 — Quantos pedidos CONCLUIDOS foram realizados pelo canal SITE de 1º de janeiro a 30 de setembro de 2026, inclusive?
SELECT COUNT(*) AS pedidos_site_2026
FROM dataset.pedidos
WHERE status = 'CONCLUIDO'
  AND canal_venda = 'SITE'
  AND data_pedido >= DATE '2026-01-01'
  AND data_pedido < DATE '2026-10-01';
