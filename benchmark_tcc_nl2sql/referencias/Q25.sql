-- Q25 — Quantos clientes fizeram pelo menos uma compra CONCLUIDA em 2024, mas nenhuma compra CONCLUIDA em 2025? Compras em outros anos não impedem a inclusão.
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
