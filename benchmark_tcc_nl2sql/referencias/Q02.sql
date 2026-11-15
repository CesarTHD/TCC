-- Q02 — Quantos produtos estão ativos no catálogo?
SELECT COUNT(*) AS produtos_ativos
FROM dataset.produtos
WHERE ativo = TRUE;
