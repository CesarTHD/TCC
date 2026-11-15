-- Q08 — Quantos clientes do segmento PREMIUM, com status ATIVO, estão cadastrados na UF DF?
SELECT COUNT(*) AS clientes_premium_ativos_df
FROM dataset.clientes
WHERE segmento = 'PREMIUM'
  AND status = 'ATIVO'
  AND uf = 'DF';
