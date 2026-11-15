-- Q10 — Quantas cidades distintas possuem clientes cadastrados na UF SP?
SELECT COUNT(DISTINCT cidade) AS cidades_distintas_sp
FROM dataset.clientes
WHERE uf = 'SP';
