-- Q17 — Quantos clientes cadastrados nunca realizaram um pedido CONCLUIDO até 30 de setembro de 2026, inclusive?
SELECT COUNT(*) AS clientes_sem_compra_concluida
FROM dataset.clientes c
WHERE NOT EXISTS (
    SELECT 1
    FROM dataset.pedidos p
    WHERE p.cliente_id = c.id
      AND p.status = 'CONCLUIDO'
      AND p.data_pedido < DATE '2026-10-01'
);
