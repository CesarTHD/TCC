"""Gerador determinístico do dataset experimental.

`generate()` é uma função pura: dada a mesma seed devolve exatamente as mesmas
linhas (tuplas na ordem das colunas de database/schema.sql). Não acessa banco,
relógio do sistema nem serviços externos.

Toda a aleatoriedade vem de uma única instância `random.Random(seed)`, consumida
sempre na mesma ordem: categorias -> produtos -> vendedores -> clientes -> pedidos/itens.
"""

from __future__ import annotations

import hashlib
import math
import random
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from reference_data import (
    CANAIS, CATEGORIAS, CIDADES, DISTRIBUICAO_ITENS, EMAIL_DOMINIO_CLIENTES,
    EMAIL_DOMINIO_VENDEDORES, FAIXAS_PENDENTE, INFLACAO_ANUAL, MULTIPLICADOR_LINHA,
    PERCENTUAIS_DESCONTO, PERFIS_COMPRA, PESO_CANAL_POR_ANO, PESO_MES, POPULARIDADE_LINHA,
    PRENOMES, PROB_CANCELAMENTO, PROB_DESCONTO, REGIAO_POR_UF, SOBRENOMES,
    VENDEDORES_POR_REGIAO,
)

SEED = 42
DATA_REFERENCIA = date(2026, 9, 30)
INICIO_PEDIDOS = date(2023, 1, 1)
NUM_CLIENTES = 2000
CENTAVO = Decimal("0.01")

# Ordem das colunas de cada tabela (igual a database/schema.sql)
COLUNAS = {
    "categorias": ("id", "nome", "descricao"),
    "produtos": ("id", "categoria_id", "nome", "descricao", "preco", "ativo", "data_cadastro"),
    "clientes": ("id", "nome", "email", "data_nascimento", "data_cadastro", "cidade", "uf",
                 "segmento", "status"),
    "vendedores": ("id", "nome", "email", "data_admissao", "data_desligamento", "regiao", "status"),
    "pedidos": ("id", "cliente_id", "vendedor_id", "data_pedido", "status", "canal_venda",
                "valor_total"),
    "itens_pedido": ("id", "pedido_id", "produto_id", "quantidade", "preco_unitario", "desconto",
                     "valor_total_item"),
}
# Ordem de inserção respeitando as FKs
ORDEM_TABELAS = ("categorias", "produtos", "vendedores", "clientes", "pedidos", "itens_pedido")


@dataclass
class Dataset:
    tables: dict[str, list[tuple]] = field(default_factory=dict)

    def digest(self) -> str:
        """SHA-256 da representação canônica de todas as linhas (para checar determinismo)."""
        h = hashlib.sha256()
        for name in ORDEM_TABELAS:
            h.update(name.encode())
            for row in self.tables[name]:
                h.update(repr(row).encode())
        return h.hexdigest()

    def counts(self) -> dict[str, int]:
        return {name: len(self.tables[name]) for name in ORDEM_TABELAS}


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------
def money(value) -> Decimal:
    return Decimal(str(value)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def random_date(rng: random.Random, start: date, end: date) -> date:
    """Data uniforme no intervalo fechado [start, end]."""
    return start + timedelta(days=rng.randint(0, (end - start).days))


def ascii_slug(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if c.isascii() and c.isalnum()).lower()


def poisson(rng: random.Random, lam: float) -> int:
    """Amostra Poisson (algoritmo de Knuth; lam <= ~60 neste dataset)."""
    if lam <= 0:
        return 0
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def weighted_choice(rng: random.Random, items, weights):
    return rng.choices(items, weights=weights, k=1)[0]


def person_name(rng: random.Random) -> tuple[str, str, str]:
    first = rng.choice(PRENOMES)
    last1, last2 = rng.sample(SOBRENOMES, 2)
    return first, last2, f"{first} {last1} {last2}"


# ---------------------------------------------------------------------------
# Etapas de geração
# ---------------------------------------------------------------------------
def gen_categorias_produtos(rng: random.Random):
    categorias, produtos, meta = [], [], []
    pid = 0
    for cid, cat in enumerate(CATEGORIAS, start=1):
        categorias.append((cid, cat["nome"], cat["descricao"]))
        # Popularidade dentro da categoria: lei de potência sobre um ranking embaralhado
        n_cat = len(cat["itens"]) * len(cat["marcas"])
        ranks = list(range(n_cat))
        rng.shuffle(ranks)
        k = 0
        for base, pmin, pmax in cat["itens"]:
            base_price = rng.uniform(pmin, pmax)
            for linha, marca in enumerate(cat["marcas"]):
                pid += 1
                preco = money(max(round(base_price * MULTIPLICADOR_LINHA[linha]), 1) - 0.10)
                # 65% dos produtos já existiam antes de 2023; os demais entram ao longo do período
                if rng.random() < 0.65:
                    cadastro = random_date(rng, date(2021, 3, 1), date(2022, 12, 31))
                else:
                    cadastro = random_date(rng, date(2023, 1, 1), date(2026, 8, 31))
                # Popularidade = categoria x linha x ranking (lei de potência) / sqrt(preço):
                # itens caros são comprados com menos frequência que itens baratos.
                popularidade = (cat["popularidade"] * POPULARIDADE_LINHA[linha]
                                / (ranks[k] + 1) ** 0.8 / math.sqrt(float(preco) / 100))
                k += 1
                nome = f"{base} {marca}"
                descricao = f"{base} da marca {marca} ({['linha econômica', 'linha intermediária', 'linha premium'][linha]})."
                produtos.append([pid, cid, nome, descricao, preco, True, cadastro])
                meta.append({"id": pid, "cadastro": cadastro, "fim_vendas": DATA_REFERENCIA,
                             "preco": preco, "peso": popularidade})

    # ~8% dos produtos são descontinuados (inativos): vendem somente até uma data interna
    elegiveis = [m for m in meta if m["cadastro"] <= date(2025, 6, 30)]
    for m in rng.sample(elegiveis, 18):
        inicio = max(m["cadastro"] + timedelta(days=180), date(2024, 1, 1))
        m["fim_vendas"] = random_date(rng, inicio, date(2026, 6, 30))
        produtos[m["id"] - 1][5] = False
    return categorias, [tuple(p) for p in produtos], meta


def gen_vendedores(rng: random.Random):
    vendedores, meta = [], []
    vid = 0
    usados: set[str] = set()
    for regiao, qtd in VENDEDORES_POR_REGIAO:
        for i in range(qtd):
            vid += 1
            first, last, nome = person_name(rng)
            email = f"{ascii_slug(first)}.{ascii_slug(last)}@{EMAIL_DOMINIO_VENDEDORES}"
            if email in usados:
                email = f"{ascii_slug(first)}.{ascii_slug(last)}{vid}@{EMAIL_DOMINIO_VENDEDORES}"
            usados.add(email)
            # Os 2 primeiros de cada região são veteranos que permanecem ativos (garante
            # vendedor disponível em todas as regiões durante todo o período).
            if i < 2 or rng.random() < 0.55:
                admissao = random_date(rng, date(2016, 1, 1), date(2022, 10, 31))
            else:
                admissao = random_date(rng, date(2023, 2, 1), date(2025, 12, 31))
            vendedores.append([vid, nome, email, admissao, None, regiao, "ATIVO"])
            # Desempenho heterogêneo: peso log-normal => volumes de venda bem diferentes
            meta.append({"id": vid, "regiao": regiao, "inicio": admissao, "fim": DATA_REFERENCIA,
                         "peso": rng.lognormvariate(0, 0.6), "veterano_fixo": i < 2})

    # Exatamente 4 vendedores desligados (INATIVO), escolhidos entre os não fixos
    # admitidos antes de 2023: vendem somente até a data de desligamento.
    elegiveis = [m for m in meta if not m["veterano_fixo"] and m["inicio"] < date(2023, 1, 1)]
    for m in rng.sample(elegiveis, 4):
        m["fim"] = random_date(rng, date(2024, 3, 1), date(2026, 6, 30))
        vendedores[m["id"] - 1][4] = m["fim"]
        vendedores[m["id"] - 1][6] = "INATIVO"
    return [tuple(v) for v in vendedores], meta


def gen_clientes(rng: random.Random):
    clientes, meta = [], []
    cidades = [(c, uf) for c, uf, _ in CIDADES]
    pesos_cidade = [w for _, _, w in CIDADES]
    for cid in range(1, NUM_CLIENTES + 1):
        first, last, nome = person_name(rng)
        email = f"{ascii_slug(first)}.{ascii_slug(last)}.{cid}@{EMAIL_DOMINIO_CLIENTES}"
        # 22% da base já existia antes de 2023; o restante entra com crescimento ao longo do tempo
        if rng.random() < 0.22:
            cadastro = random_date(rng, date(2021, 1, 1), date(2022, 12, 31))
        else:
            span = (DATA_REFERENCIA - INICIO_PEDIDOS).days
            u = rng.random() if rng.random() < 0.5 else rng.triangular(0, 1, 1)
            cadastro = INICIO_PEDIDOS + timedelta(days=int(u * span))
        idade = rng.triangular(18, 75, 32)
        nascimento = cadastro - timedelta(days=int(idade * 365.25))
        cidade, uf = weighted_choice(rng, cidades, pesos_cidade)
        segmento = "PREMIUM" if rng.random() < 0.15 else "PADRAO"
        status = "INATIVO" if rng.random() < 0.10 else "ATIVO"   # independente das compras
        idx_peso = 1 if segmento == "PADRAO" else 2
        perfil = weighted_choice(rng, PERFIS_COMPRA, [p[idx_peso] for p in PERFIS_COMPRA])[0]
        clientes.append((cid, nome, email, nascimento, cadastro, cidade, uf, segmento, status))
        meta.append({"id": cid, "cadastro": cadastro, "regiao": REGIAO_POR_UF[uf],
                     "segmento": segmento, "perfil": perfil})
    return clientes, meta


def sample_order_date(rng: random.Random, start: date, end: date) -> date:
    """Data em [start, end] com sazonalidade mensal moderada (amostragem por rejeição)."""
    max_w = max(PESO_MES.values())
    while True:
        d = random_date(rng, start, end)
        if rng.random() < PESO_MES[d.month] / max_w:
            return d


def historical_price(preco_atual: Decimal, d: date) -> Decimal:
    """Preço praticado em `d`: preço atual deflacionado pela inflação anual."""
    anos = (DATA_REFERENCIA - d).days / 365.25
    return money(float(preco_atual) / (1 + INFLACAO_ANUAL) ** anos)


def gen_pedidos(rng, clientes_meta, vendedores_meta, produtos_meta):
    itens_k = [k for k, _ in DISTRIBUICAO_ITENS]
    itens_w = [w for _, w in DISTRIBUICAO_ITENS]
    pct_k = [p for p, _ in PERCENTUAIS_DESCONTO]
    pct_w = [w for _, w in PERCENTUAIS_DESCONTO]
    taxas = {p[0]: p[3] for p in PERFIS_COMPRA}

    rascunhos = []  # (data, cliente_id, seq, vendedor_id, status, canal, itens)
    for c in clientes_meta:
        inicio = max(c["cadastro"], INICIO_PEDIDOS)
        anos = ((DATA_REFERENCIA - inicio).days + 1) / 365.25
        perfil = c["perfil"]
        if perfil == "nunca":
            n = 0
        elif perfil == "unico":
            n = 1
        else:
            n = poisson(rng, taxas[perfil] * anos)
        datas = sorted(sample_order_date(rng, inicio, DATA_REFERENCIA) for _ in range(n))

        for seq, d in enumerate(datas):
            # Vendedor: ativo na data, preferencialmente da região do cliente (75%)
            ativos = [v for v in vendedores_meta if v["inicio"] <= d <= v["fim"]]
            da_regiao = [v for v in ativos if v["regiao"] == c["regiao"]]
            pool = da_regiao if da_regiao and rng.random() < 0.75 else ativos
            vendedor = weighted_choice(rng, pool, [v["peso"] for v in pool])

            canal = weighted_choice(rng, CANAIS, PESO_CANAL_POR_ANO[d.year])
            idade = (DATA_REFERENCIA - d).days
            status = None
            for limite, prob in FAIXAS_PENDENTE:
                if idade <= limite:
                    if rng.random() < prob:
                        status = "PENDENTE"
                    break
            if status is None:
                status = "CANCELADO" if rng.random() < PROB_CANCELAMENTO[canal] else "CONCLUIDO"

            # Itens: produtos disponíveis na data, sorteados por popularidade sem reposição
            disponiveis = [p for p in produtos_meta if p["cadastro"] <= d <= p["fim_vendas"]]
            pesos = [p["peso"] for p in disponiveis]
            k = min(weighted_choice(rng, itens_k, itens_w), len(disponiveis))
            itens = []
            for _ in range(k):
                idx = rng.choices(range(len(disponiveis)), weights=pesos, k=1)[0]
                prod = disponiveis.pop(idx)
                pesos.pop(idx)
                preco_unit = historical_price(prod["preco"], d)
                if preco_unit < 100:
                    qtd = weighted_choice(rng, (1, 2, 3, 4, 5, 6), (40, 25, 15, 10, 5, 5))
                elif preco_unit < 500:
                    qtd = weighted_choice(rng, (1, 2, 3), (75, 20, 5))
                else:
                    qtd = weighted_choice(rng, (1, 2), (90, 10))
                bruto = preco_unit * qtd
                desconto = Decimal("0.00")
                if rng.random() < PROB_DESCONTO[c["segmento"]]:
                    pct = weighted_choice(rng, pct_k, pct_w)
                    desconto = money(bruto * pct / 100)
                itens.append((prod["id"], qtd, preco_unit, desconto, bruto - desconto))
            rascunhos.append((d, c["id"], seq, vendedor["id"], status, canal, itens))

    # IDs em ordem cronológica (data, cliente, sequência)
    rascunhos.sort(key=lambda r: (r[0], r[1], r[2]))
    pedidos, itens_pedido = [], []
    item_id = 0
    for pedido_id, (d, cliente_id, _, vendedor_id, status, canal, itens) in enumerate(rascunhos, start=1):
        total = Decimal("0.00")
        for produto_id, qtd, preco_unit, desconto, valor_item in itens:
            item_id += 1
            itens_pedido.append((item_id, pedido_id, produto_id, qtd, preco_unit, desconto, valor_item))
            total += valor_item
        pedidos.append((pedido_id, cliente_id, vendedor_id, d, status, canal, total))
    return pedidos, itens_pedido


def generate(seed: int = SEED) -> Dataset:
    rng = random.Random(seed)
    categorias, produtos, produtos_meta = gen_categorias_produtos(rng)
    vendedores, vendedores_meta = gen_vendedores(rng)
    clientes, clientes_meta = gen_clientes(rng)
    pedidos, itens = gen_pedidos(rng, clientes_meta, vendedores_meta, produtos_meta)
    return Dataset(tables={
        "categorias": categorias,
        "produtos": produtos,
        "vendedores": vendedores,
        "clientes": clientes,
        "pedidos": pedidos,
        "itens_pedido": itens,
    })


if __name__ == "__main__":
    ds = generate()
    for name, n in ds.counts().items():
        print(f"{name:14s} {n:>7d}")
    print("digest", ds.digest())
