-- Q09 — Qual é o maior preço de tabela atual entre os produtos ativos?
SELECT MAX(preco) AS maior_preco_atual
FROM dataset.produtos
WHERE ativo = TRUE;
