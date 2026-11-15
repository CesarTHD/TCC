-- Q19 — Quantos pedidos CONCLUIDOS foram realizados em 2025 por clientes de cada segmento de fidelidade? Mostre apenas segmentos com pedidos, ordenados pelo nome do segmento.
SELECT c.segmento,
       COUNT(p.id) AS total_pedidos
FROM dataset.clientes c
JOIN dataset.pedidos p ON p.cliente_id = c.id
WHERE p.status = 'CONCLUIDO'
  AND p.data_pedido >= DATE '2025-01-01'
  AND p.data_pedido < DATE '2026-01-01'
GROUP BY c.segmento
ORDER BY c.segmento;
