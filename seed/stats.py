"""Gera docs/dataset_statistics.md com estatísticas REAIS consultadas no banco.

Uso (a partir da raiz do repositório, após o seed):
    python seed/stats.py
"""

from __future__ import annotations

from decimal import Decimal

from db import ROOT, checksums, connect
from generator import DATA_REFERENCIA, SEED, generate

SAIDA = ROOT / "docs" / "dataset_statistics.md"


def fmt(v) -> str:
    if isinstance(v, Decimal):
        if v == v.to_integral_value() and v.as_tuple().exponent == 0:
            return f"{int(v):,}".replace(",", ".")
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    return "—" if v is None else str(v)


def table(conn, sql: str, headers: list[str]) -> str:
    rows = conn.execute(sql).fetchall()
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(fmt(v) for v in r) + " |" for r in rows]
    return "\n".join(out)


def scalar(conn, sql: str):
    return conn.execute(sql).fetchone()[0]


SQL = {
    "contagens": """
        SELECT 'categorias', count(*) FROM dataset.categorias UNION ALL
        SELECT 'produtos', count(*) FROM dataset.produtos UNION ALL
        SELECT 'vendedores', count(*) FROM dataset.vendedores UNION ALL
        SELECT 'clientes', count(*) FROM dataset.clientes UNION ALL
        SELECT 'pedidos', count(*) FROM dataset.pedidos UNION ALL
        SELECT 'itens_pedido', count(*) FROM dataset.itens_pedido""",
    "periodos": """
        SELECT 'pedidos.data_pedido', min(data_pedido), max(data_pedido) FROM dataset.pedidos UNION ALL
        SELECT 'clientes.data_cadastro', min(data_cadastro), max(data_cadastro) FROM dataset.clientes UNION ALL
        SELECT 'produtos.data_cadastro', min(data_cadastro), max(data_cadastro) FROM dataset.produtos UNION ALL
        SELECT 'vendedores.data_admissao', min(data_admissao), max(data_admissao) FROM dataset.vendedores""",
    "status": """
        SELECT status, count(*), round(100.0 * count(*) / sum(count(*)) OVER (), 2), sum(valor_total)
        FROM dataset.pedidos GROUP BY status ORDER BY count(*) DESC""",
    "anos": """
        SELECT extract(year FROM data_pedido)::int::text, count(*),
               count(*) FILTER (WHERE status = 'CONCLUIDO'),
               count(*) FILTER (WHERE status = 'CANCELADO'),
               count(*) FILTER (WHERE status = 'PENDENTE'),
               sum(valor_total) FILTER (WHERE status = 'CONCLUIDO')
        FROM dataset.pedidos GROUP BY 1 ORDER BY 1""",
    "canais": """
        SELECT canal_venda, count(*), round(100.0 * count(*) / sum(count(*)) OVER (), 2),
               round(100.0 * count(*) FILTER (WHERE status = 'CANCELADO') / count(*), 2)
        FROM dataset.pedidos GROUP BY canal_venda ORDER BY count(*) DESC""",
    "canal_ano": """
        SELECT extract(year FROM data_pedido)::int::text,
               round(100.0 * count(*) FILTER (WHERE canal_venda = 'SITE') / count(*), 1),
               round(100.0 * count(*) FILTER (WHERE canal_venda = 'LOJA') / count(*), 1),
               round(100.0 * count(*) FILTER (WHERE canal_venda = 'APP') / count(*), 1),
               round(100.0 * count(*) FILTER (WHERE canal_venda = 'TELEFONE') / count(*), 1)
        FROM dataset.pedidos GROUP BY 1 ORDER BY 1""",
    "meses": """
        SELECT extract(month FROM data_pedido)::int,
               count(*) FILTER (WHERE extract(year FROM data_pedido) = 2023),
               count(*) FILTER (WHERE extract(year FROM data_pedido) = 2024),
               count(*) FILTER (WHERE extract(year FROM data_pedido) = 2025),
               count(*) FILTER (WHERE extract(year FROM data_pedido) = 2026)
        FROM dataset.pedidos GROUP BY 1 ORDER BY 1""",
    "uf": """
        SELECT uf, count(*), round(100.0 * count(*) / sum(count(*)) OVER (), 2)
        FROM dataset.clientes GROUP BY uf ORDER BY count(*) DESC, uf""",
    "clientes_faixa": """
        SELECT CASE WHEN n = 0 THEN '0 pedidos' WHEN n = 1 THEN '1 pedido' WHEN n <= 5 THEN '2 a 5'
                    WHEN n <= 20 THEN '6 a 20' ELSE '21 ou mais' END, count(*)
        FROM (SELECT c.id, count(p.id) AS n FROM dataset.clientes c
              LEFT JOIN dataset.pedidos p ON p.cliente_id = c.id GROUP BY c.id) t
        GROUP BY 1 ORDER BY min(n)""",
    "clientes_attr": """
        SELECT 'segmento', segmento, count(*) FROM dataset.clientes GROUP BY segmento UNION ALL
        SELECT 'status', status, count(*) FROM dataset.clientes GROUP BY status ORDER BY 1, 2""",
    "itens_por_pedido": """
        SELECT itens, count(*) FROM (SELECT pedido_id, count(*) AS itens FROM dataset.itens_pedido
        GROUP BY pedido_id) t GROUP BY itens ORDER BY itens""",
    "categorias": """
        SELECT ca.nome, count(DISTINCT pr.id), sum(i.quantidade), sum(i.valor_total_item),
               round(100.0 * sum(i.valor_total_item) / sum(sum(i.valor_total_item)) OVER (), 2)
        FROM dataset.itens_pedido i
        JOIN dataset.pedidos p ON p.id = i.pedido_id AND p.status = 'CONCLUIDO'
        JOIN dataset.produtos pr ON pr.id = i.produto_id
        JOIN dataset.categorias ca ON ca.id = pr.categoria_id
        GROUP BY ca.nome ORDER BY 4 DESC""",
    "top_produtos_qtd": """
        SELECT pr.nome, ca.nome, sum(i.quantidade), sum(i.valor_total_item)
        FROM dataset.itens_pedido i
        JOIN dataset.pedidos p ON p.id = i.pedido_id AND p.status = 'CONCLUIDO'
        JOIN dataset.produtos pr ON pr.id = i.produto_id
        JOIN dataset.categorias ca ON ca.id = pr.categoria_id
        GROUP BY pr.nome, ca.nome ORDER BY 3 DESC, 1 LIMIT 10""",
    "top_produtos_fat": """
        SELECT pr.nome, ca.nome, sum(i.quantidade), sum(i.valor_total_item)
        FROM dataset.itens_pedido i
        JOIN dataset.pedidos p ON p.id = i.pedido_id AND p.status = 'CONCLUIDO'
        JOIN dataset.produtos pr ON pr.id = i.produto_id
        JOIN dataset.categorias ca ON ca.id = pr.categoria_id
        GROUP BY pr.nome, ca.nome ORDER BY 4 DESC, 1 LIMIT 10""",
    "vendedores": """
        SELECT v.nome, v.regiao, v.status, count(p.id), sum(p.valor_total)
        FROM dataset.vendedores v
        LEFT JOIN dataset.pedidos p ON p.vendedor_id = v.id AND p.status = 'CONCLUIDO'
        GROUP BY v.id, v.nome, v.regiao, v.status ORDER BY 5 DESC NULLS LAST""",
    "produtos": """
        SELECT CASE WHEN ativo THEN 'ativos' ELSE 'inativos' END, count(*) FROM dataset.produtos
        GROUP BY ativo ORDER BY ativo DESC""",
}


def main() -> None:
    ds_digest = generate(SEED).digest()
    with connect() as c:
        fat = scalar(c, "SELECT sum(valor_total) FROM dataset.pedidos WHERE status = 'CONCLUIDO'")
        ticket = scalar(c, "SELECT round(avg(valor_total), 2) FROM dataset.pedidos WHERE status = 'CONCLUIDO'")
        ticket_med = scalar(c, """SELECT percentile_disc(0.5) WITHIN GROUP (ORDER BY valor_total)
                                  FROM dataset.pedidos WHERE status = 'CONCLUIDO'""")
        sem_pedido = scalar(c, """SELECT count(*) FROM dataset.clientes c WHERE NOT EXISTS
                                  (SELECT 1 FROM dataset.pedidos p WHERE p.cliente_id = c.id)""")
        compraram = scalar(c, "SELECT count(DISTINCT cliente_id) FROM dataset.pedidos WHERE status = 'CONCLUIDO'")
        com_pedido_sem_compra = scalar(c, """
            SELECT count(*) FROM dataset.clientes c
            WHERE EXISTS (SELECT 1 FROM dataset.pedidos p WHERE p.cliente_id = c.id)
              AND NOT EXISTS (SELECT 1 FROM dataset.pedidos p WHERE p.cliente_id = c.id AND p.status = 'CONCLUIDO')""")
        max_pedidos = scalar(c, "SELECT max(n) FROM (SELECT count(*) AS n FROM dataset.pedidos GROUP BY cliente_id) t")
        desconto = c.execute("""
            SELECT round(100.0 * count(*) FILTER (WHERE desconto > 0) / count(*), 2), sum(desconto)
            FROM dataset.itens_pedido i JOIN dataset.pedidos p ON p.id = i.pedido_id
            WHERE p.status = 'CONCLUIDO'""").fetchone()
        nunca_vendidos = scalar(c, """SELECT count(*) FROM dataset.produtos pr WHERE NOT EXISTS
            (SELECT 1 FROM dataset.itens_pedido i WHERE i.produto_id = pr.id)""")
        ufs_sem = scalar(c, "SELECT 27 - count(DISTINCT uf) FROM dataset.clientes")
        cks = checksums(c)

        md = f"""# Estatísticas do dataset

> Documento **gerado automaticamente** por `python seed/stats.py` a partir de consultas
> executadas no banco populado (seed = {SEED}, data de referência = {DATA_REFERENCIA}).
> Não editar à mão.
>
> **Uso metodológico:** este documento descreve o dataset para o texto do TCC. Ele
> **não** deve ser fornecido como contexto às arquiteturas NL2SQL avaliadas, pois
> contém resultados agregados que poderiam funcionar como gabarito.

Regras usadas nos números abaixo (ver `metadata/business_rules.json`): faturamento,
ticket médio e quantidade vendida consideram apenas pedidos `CONCLUIDO`.

## 1. Registros por tabela

{table(c, SQL["contagens"], ["tabela", "registros"])}

## 2. Período coberto

{table(c, SQL["periodos"], ["coluna", "mínimo", "máximo"])}

Cadastros de clientes, produtos e vendedores podem ser anteriores a 2023 (base pré-existente);
pedidos existem somente de 2023-01-01 a 2026-09-30. O ano de 2026 está incompleto (jan–set).

## 3. Indicadores gerais

| indicador | valor |
|---|---|
| Faturamento total (pedidos CONCLUIDO) | R$ {fmt(fat)} |
| Ticket médio (pedidos CONCLUIDO) | R$ {fmt(ticket)} |
| Ticket mediano (pedidos CONCLUIDO) | R$ {fmt(ticket_med)} |
| Clientes sem nenhum pedido | {fmt(sem_pedido)} |
| Clientes com pelo menos um pedido CONCLUIDO (compraram) | {fmt(compraram)} |
| Clientes com pedidos, mas nenhum CONCLUIDO | {fmt(com_pedido_sem_compra)} |
| Maior número de pedidos de um único cliente | {fmt(max_pedidos)} |
| Itens (de pedidos CONCLUIDO) com desconto | {fmt(desconto[0])}% |
| Total de descontos concedidos (pedidos CONCLUIDO) | R$ {fmt(desconto[1])} |
| Produtos nunca vendidos | {fmt(nunca_vendidos)} |
| UFs sem clientes | {fmt(ufs_sem)} |

## 4. Pedidos por status

{table(c, SQL["status"], ["status", "pedidos", "%", "soma de valor_total (R$)"])}

## 5. Pedidos por ano

{table(c, SQL["anos"], ["ano", "pedidos", "concluídos", "cancelados", "pendentes", "faturamento (R$)"])}

## 6. Pedidos por mês e ano (sazonalidade)

{table(c, SQL["meses"], ["mês", "2023", "2024", "2025", "2026"])}

## 7. Pedidos por canal de venda

{table(c, SQL["canais"], ["canal", "pedidos", "% dos pedidos", "% cancelados no canal"])}

Participação (%) dos canais por ano:

{table(c, SQL["canal_ano"], ["ano", "SITE", "LOJA", "APP", "TELEFONE"])}

## 8. Clientes por UF

{table(c, SQL["uf"], ["UF", "clientes", "%"])}

## 9. Clientes por quantidade de pedidos (qualquer status)

{table(c, SQL["clientes_faixa"], ["faixa", "clientes"])}

Atributos cadastrais:

{table(c, SQL["clientes_attr"], ["atributo", "valor", "clientes"])}

## 10. Pedidos por quantidade de itens

{table(c, SQL["itens_por_pedido"], ["itens no pedido", "pedidos"])}

## 11. Categorias (pedidos CONCLUIDO)

{table(c, SQL["categorias"], ["categoria", "produtos vendidos", "unidades", "faturamento (R$)", "% do faturamento"])}

## 12. Top 10 produtos por quantidade vendida

{table(c, SQL["top_produtos_qtd"], ["produto", "categoria", "unidades", "faturamento (R$)"])}

## 13. Top 10 produtos por faturamento

{table(c, SQL["top_produtos_fat"], ["produto", "categoria", "unidades", "faturamento (R$)"])}

## 14. Vendedores (pedidos CONCLUIDO), ordenados por faturamento

{table(c, SQL["vendedores"], ["vendedor", "região", "status", "vendas", "faturamento (R$)"])}

## 15. Produtos ativos e inativos

{table(c, SQL["produtos"], ["situação", "produtos"])}

## 16. Checksums de reprodutibilidade

Digest SHA-256 do gerador (Python): `{ds_digest}`

MD5 do conteúdo de cada tabela (`database/checksums.sql`):

| tabela | linhas | md5 |
|---|---|---|
""" + "\n".join(f"| {t} | {fmt(n)} | `{m}` |" for t, n, m in cks) + "\n"

    SAIDA.write_text(md, encoding="utf-8", newline="\n")
    print(f"Gerado {SAIDA.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
