"""Testes do gerador (não precisam de banco de dados)."""

from collections import Counter
from datetime import date

from generator import DATA_REFERENCIA, INICIO_PEDIDOS, generate


def by_id(rows):
    return {r[0]: r for r in rows}


def test_determinismo(dataset):
    assert generate(42).digest() == dataset.digest()


def test_seed_diferente_gera_dados_diferentes(dataset):
    assert generate(7).digest() != dataset.digest()


def test_volumes_aproximados(dataset):
    n = dataset.counts()
    assert n["clientes"] == 2000
    assert 20 <= n["vendedores"] <= 30
    assert 8 <= n["categorias"] <= 12
    assert 150 <= n["produtos"] <= 250
    assert 10_000 <= n["pedidos"] <= 15_000
    assert 30_000 <= n["itens_pedido"] <= 50_000


def test_ids_unicos_e_sequenciais(dataset):
    for rows in dataset.tables.values():
        assert [r[0] for r in rows] == list(range(1, len(rows) + 1))


def test_integridade_referencial(dataset):
    t = dataset.tables
    categorias, clientes = by_id(t["categorias"]), by_id(t["clientes"])
    vendedores, produtos, pedidos = by_id(t["vendedores"]), by_id(t["produtos"]), by_id(t["pedidos"])
    assert all(p[1] in categorias for p in t["produtos"])
    assert all(p[1] in clientes and p[2] in vendedores for p in t["pedidos"])
    assert all(i[1] in pedidos and i[2] in produtos for i in t["itens_pedido"])
    assert {i[1] for i in t["itens_pedido"]} == set(pedidos)  # todo pedido tem item
    pares = [(i[1], i[2]) for i in t["itens_pedido"]]
    assert len(pares) == len(set(pares))  # produto no máximo 1x por pedido


def test_regras_financeiras(dataset):
    t = dataset.tables
    soma = Counter()
    for _, pedido_id, _, qtd, preco, desconto, valor in t["itens_pedido"]:
        assert qtd > 0 and preco > 0 and desconto >= 0
        assert desconto <= qtd * preco
        assert valor == qtd * preco - desconto
        for v in (preco, desconto, valor):
            assert v == v.quantize(preco.__class__("0.01"))  # 2 casas decimais
        soma[pedido_id] += valor
    for p in t["pedidos"]:
        assert p[6] == soma[p[0]]
    assert all(p[4] > 0 for p in t["produtos"])


def test_limites_temporais(dataset):
    t = dataset.tables
    clientes, vendedores = by_id(t["clientes"]), by_id(t["vendedores"])
    produtos, pedidos = by_id(t["produtos"]), by_id(t["pedidos"])
    for p in t["pedidos"]:
        d = p[3]
        assert INICIO_PEDIDOS <= d <= DATA_REFERENCIA
        assert d >= clientes[p[1]][4]
        v = vendedores[p[2]]
        assert d >= v[3] and (v[4] is None or d <= v[4])
    for i in t["itens_pedido"]:
        assert pedidos[i[1]][3] >= produtos[i[2]][6]
    for c in t["clientes"]:
        assert c[3] < c[4] <= DATA_REFERENCIA
        assert (c[4] - c[3]).days >= 18 * 365
    assert all(p[6] <= DATA_REFERENCIA for p in t["produtos"])
    assert all(v[3] <= DATA_REFERENCIA and (v[4] is None or v[3] < v[4] <= DATA_REFERENCIA)
               for v in t["vendedores"])


def test_regras_categoricas(dataset):
    t = dataset.tables
    assert {p[4] for p in t["pedidos"]} == {"CONCLUIDO", "CANCELADO", "PENDENTE"}
    assert {p[5] for p in t["pedidos"]} == {"SITE", "LOJA", "APP", "TELEFONE"}
    assert {c[7] for c in t["clientes"]} == {"PADRAO", "PREMIUM"}
    assert {c[8] for c in t["clientes"]} == {"ATIVO", "INATIVO"}
    assert {v[5] for v in t["vendedores"]} == {"NORTE", "NORDESTE", "CENTRO-OESTE", "SUDESTE", "SUL"}
    for v in t["vendedores"]:
        assert (v[6] == "INATIVO") == (v[4] is not None)
    assert {p[5] for p in t["produtos"]} == {True, False}
    # Pedidos pendentes só existem nos últimos 45 dias antes da referência
    assert all((DATA_REFERENCIA - p[3]).days <= 45 for p in t["pedidos"] if p[4] == "PENDENTE")


def test_caracteristicas_nao_uniformes(dataset):
    t = dataset.tables
    por_cliente = Counter(p[1] for p in t["pedidos"])
    n = [por_cliente.get(c[0], 0) for c in t["clientes"]]
    assert n.count(0) > 0 and n.count(1) > 0 and max(n) >= 30
    itens_por_pedido = Counter(i[1] for i in t["itens_pedido"])
    assert min(itens_por_pedido.values()) == 1 and max(itens_por_pedido.values()) >= 8
    anos = Counter(p[3].year for p in t["pedidos"])
    assert set(anos) == {2023, 2024, 2025, 2026}
    ufs = Counter(c[6] for c in t["clientes"])
    assert ufs.most_common(1)[0][0] == "SP" and len(ufs) >= 20
    por_vendedor = Counter(p[2] for p in t["pedidos"])
    assert max(por_vendedor.values()) >= 4 * min(por_vendedor.values())


def test_dados_ficticios(dataset):
    emails = [c[2] for c in dataset.tables["clientes"]] + [v[2] for v in dataset.tables["vendedores"]]
    assert len(emails) == len(set(emails))
    assert all(e.endswith("example.com") for e in emails)


def test_sem_data_atual():
    # Nenhuma data gerada depende do relógio: a referência é fixa
    assert DATA_REFERENCIA == date(2026, 9, 30)
