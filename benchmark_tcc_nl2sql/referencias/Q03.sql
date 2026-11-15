-- Q03 — Quantos vendedores estão atualmente com status ATIVO?
SELECT COUNT(*) AS vendedores_ativos
FROM dataset.vendedores
WHERE status = 'ATIVO';
