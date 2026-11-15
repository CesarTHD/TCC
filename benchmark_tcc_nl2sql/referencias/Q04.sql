-- Q04 — Quantos pedidos com status CANCELADO foram registrados durante o ano de 2025?
SELECT COUNT(*) AS pedidos_cancelados
FROM dataset.pedidos
WHERE status = 'CANCELADO'
  AND data_pedido >= DATE '2025-01-01'
  AND data_pedido < DATE '2026-01-01';
