"""Documentos semânticos do RAG e cliente de embeddings (sem banco e sem rede)."""

import copy
import json
import re
import struct

import pytest

from rag import embeddings, store
from rag.documents import (BUILDER_VERSION, CATALOG_PATH, RULES_PATH, build_documents, corpus_sha256,
                           load_sources, sha256_text, source_sha256)


@pytest.fixture(scope="module")
def sources():
    return load_sources()


@pytest.fixture(scope="module")
def docs(sources):
    return build_documents(*sources)


def by_id(docs):
    return {d.doc_id: d for d in docs}


# --------------------------------------------------------------------------- estrutura

def test_quantidade_e_tipos(docs, sources):
    catalog, rules = sources
    tipos = [d.doc_type for d in docs]
    assert tipos.count("visao_geral") == 1
    assert tipos.count("tabela") == len(catalog["tabelas"]) == 6
    assert tipos.count("relacionamento") == len(catalog["relacionamentos"]) == 5
    assert tipos.count("regra") == len(rules["regras"]) == 12
    assert len(docs) == 24


def test_ids_unicos_e_estaveis(docs):
    ids = [d.doc_id for d in docs]
    assert len(ids) == len(set(ids))
    assert "tabela:pedidos" in ids and "regra:R06" in ids
    assert "relacionamento:itens_pedido.produto_id->produtos.id" in ids


def test_determinismo(sources):
    a, b = build_documents(*copy.deepcopy(sources)), build_documents(*copy.deepcopy(sources))
    assert [(d.doc_id, d.content, d.metadata) for d in a] == [(d.doc_id, d.content, d.metadata) for d in b]
    assert corpus_sha256(a) == corpus_sha256(b)


def test_hashes(docs, sources):
    for d in docs:
        assert d.content_sha256 == sha256_text(d.content)
        assert re.fullmatch(r"[0-9a-f]{64}", d.content_sha256)
        assert d.metadata["builder_version"] == BUILDER_VERSION
        assert d.metadata["schema_catalog_sha256"] == source_sha256(sources[0])
        assert d.metadata["business_rules_sha256"] == source_sha256(sources[1])


def test_hash_da_fonte_ignora_formatacao_e_fim_de_linha():
    obj = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    reformatado = json.loads(json.dumps(obj, indent=4).replace("\n", "\r\n"))
    assert source_sha256(obj) == source_sha256(reformatado)


def test_metadados_serializaveis(docs):
    for d in docs:
        assert json.loads(d.metadata_json) == d.metadata


# --------------------------------------------------------------------------- cobertura (nada se perde)

def test_tabelas_contem_todas_as_informacoes_das_colunas(docs, sources):
    catalog, _ = sources
    idx = by_id(docs)
    for t in catalog["tabelas"]:
        doc = idx[f"tabela:{t['nome']}"]
        c = doc.content
        assert f"dataset.{t['nome']}" in c
        for campo in ("descricao", "granularidade"):
            assert t[campo] in c
        for termo in t["termos"]:
            assert termo in c
        for col in t["colunas"]:
            linha = next(l for l in c.splitlines() if l.startswith(f"- {col['nome']} ("))
            assert col["tipo"] in linha and col["descricao"] in linha
            assert ("NOT NULL" in linha) is (not col["nulo"])
            assert ("PK" in linha) is bool(col.get("pk"))
            assert ("UNIQUE" in linha) is bool(col.get("unico"))
            if col.get("fk"):
                assert f"FK -> dataset.{col['fk']['tabela']}.{col['fk']['coluna']}" in linha
            for termo in col.get("termos", []):
                assert termo in linha
            for v in col.get("valores_possiveis", []):
                assert f"'{v['valor']}'" in linha
                if v.get("descricao"):
                    assert v["descricao"] in linha
            for r in col.get("regras", []):
                assert r in linha
        for r in t.get("regras", []):
            assert r in c
        assert doc.metadata["columns"] == [f"{t['nome']}.{col['nome']}" for col in t["colunas"]]


def test_relacionamentos(docs, sources):
    catalog, _ = sources
    idx = by_id(docs)
    for r in catalog["relacionamentos"]:
        doc = idx[f"relacionamento:{r['de']}->{r['para']}"]
        assert r["descricao"] in doc.content and r["cardinalidade"] in doc.content
        assert f"dataset.{r['de']} = dataset.{r['para']}" in doc.content
        for tabela in (r["de"].split(".")[0], r["para"].split(".")[0]):
            assert idx[f"tabela:{tabela}"].metadata["relationships"].count(doc.doc_id) == 1


def test_regras_completas(docs, sources):
    _, rules = sources
    idx = by_id(docs)
    for r in rules["regras"]:
        doc = idx[f"regra:{r['id']}"]
        for campo in ("id", "nome", "definicao", "definicao_sql", "observacoes"):
            assert r[campo] in doc.content, (r["id"], campo)
        for lista in ("termos", "tabelas", "colunas"):
            for item in r[lista]:
                assert item in doc.content, (r["id"], lista, item)
        assert doc.metadata["tables"] == r["tabelas"] and doc.metadata["columns"] == r["colunas"]


def test_visao_geral(docs, sources):
    catalog, rules = sources
    c = by_id(docs)["visao_geral:dataset"].content
    for valor in (catalog["banco"], catalog["schema"], catalog["sgbd"], catalog["descricao"],
                  catalog["data_referencia"], catalog["periodo_pedidos"]["inicio"],
                  catalog["periodo_pedidos"]["fim"], rules["descricao"]):
        assert valor in c
    for conv in catalog["convencoes"]:
        assert conv in c
    for r in rules["regras"]:
        assert f"{r['id']}: {r['nome']}" in c


# --------------------------------------------------------------------------- nada inventado

def test_literais_entre_aspas_vem_dos_metadados(docs, sources):
    """Todo literal '...' de documento de tabela é um valor possível de alguma coluna do catálogo."""
    catalog, _ = sources
    valores = {v["valor"] for t in catalog["tabelas"] for c in t["colunas"] for v in c.get("valores_possiveis", [])}
    for d in docs:
        if d.doc_type == "tabela":
            for linha in d.content.splitlines():
                if "Valores possíveis:" in linha:
                    trecho = linha.split("Valores possíveis:", 1)[1]
                    assert set(re.findall(r"'([^']+)'", trecho)) <= valores


def test_referencias_existem(docs, sources):
    catalog, rules = sources
    colunas = {f"{t['nome']}.{c['nome']}" for t in catalog["tabelas"] for c in t["colunas"]}
    tabelas = {t["nome"] for t in catalog["tabelas"]}
    regras = {r["id"] for r in rules["regras"]}
    for d in docs:
        assert set(d.metadata.get("tables", [])) <= tabelas
        assert set(d.metadata.get("columns", [])) <= colunas
        assert set(d.metadata.get("rule_ids", [])) <= regras


# --------------------------------------------------------------------------- incrementalidade

def test_alterar_uma_regra_muda_somente_o_texto_dela(sources):
    catalog, rules = copy.deepcopy(sources)
    antes = {d.doc_id: d.content_sha256 for d in build_documents(catalog, rules)}
    rules["regras"][4]["observacoes"] += " Texto alterado."
    depois = {d.doc_id: d.content_sha256 for d in build_documents(catalog, rules)}
    mudaram = {k for k in antes if antes[k] != depois[k]}
    assert mudaram == {f"regra:{rules['regras'][4]['id']}"}


def test_alterar_nome_de_regra_muda_os_documentos_que_a_citam(sources):
    catalog, rules = copy.deepcopy(sources)
    antes = {d.doc_id: d.content_sha256 for d in build_documents(catalog, rules)}
    rules["regras"][6]["nome"] = "Novo nome"          # R07, citada em produtos e itens_pedido
    depois = {d.doc_id: d.content_sha256 for d in build_documents(catalog, rules)}
    mudaram = {k for k in antes if antes[k] != depois[k]}
    assert mudaram == {"regra:R07", "tabela:produtos", "tabela:itens_pedido", "visao_geral:dataset"}


def _row(d, model=embeddings.MODEL, dims=embeddings.DIMENSIONS, **kw):
    row = {"doc_type": d.doc_type, "title": d.title, "content_sha256": d.content_sha256,
           "metadata": d.metadata, "embedding_model": model, "embedding_dimensions": dims}
    row.update(kw)
    return row


def test_plano(docs):
    m, n = embeddings.MODEL, embeddings.DIMENSIONS
    assert len(store.plan(docs, {}, m, n).new) == 24
    existing = {d.doc_id: _row(d) for d in docs}
    p = store.plan(docs, existing, m, n)
    assert len(p.unchanged) == 24 and not p.to_embed and not p.metadata and not p.deleted

    existing["regra:R01"] = _row(by_id(docs)["regra:R01"], content_sha256="0" * 64)
    existing["regra:R02"] = _row(by_id(docs)["regra:R02"], metadata={"x": 1})
    existing["regra:R03"] = _row(by_id(docs)["regra:R03"], model="outro-modelo")
    existing["regra:R99"] = _row(by_id(docs)["regra:R12"])
    p = store.plan(docs, existing, m, n)
    assert [d.doc_id for d in p.changed] == ["regra:R01", "regra:R03"]
    assert [d.doc_id for d in p.metadata] == ["regra:R02"]
    assert p.deleted == ["regra:R99"]
    assert len(p.unchanged) == 21


# --------------------------------------------------------------------------- vetores

def test_float32_e_hash_do_embedding():
    v = [0.1, -0.2, 1 / 3]
    v32 = store.to_float32(v)
    assert store.to_float32(v32) == v32
    assert store.parse_vector(store.vector_literal(v32)) == v32
    assert store.embedding_sha256(v32) == store.embedding_sha256(v)  # mesmo float32
    assert len(struct.pack("<3f", *v32)) == 12


# --------------------------------------------------------------------------- cliente da API (transporte falso)

class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, headers, payload, timeout):
        self.calls.append((url, headers, payload))
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def _response(n, dims=embeddings.DIMENSIONS, tokens=10, model="text-embedding-3-small"):
    return {"model": model, "usage": {"prompt_tokens": tokens, "total_tokens": tokens},
            "data": [{"index": i, "embedding": [float(i)] * dims} for i in reversed(range(n))]}


def test_cliente_monta_requisicao_e_ordena_resposta():
    t = FakeTransport([_response(3, tokens=42)])
    res = embeddings.OpenAIEmbedder(api_key="sk-test", transport=t).embed(["a", "b", "c"])
    url, headers, payload = t.calls[0]
    assert url == "https://api.openai.com/v1/embeddings"
    assert headers["Authorization"] == "Bearer sk-test"
    assert payload == {"model": "text-embedding-3-small", "input": ["a", "b", "c"], "dimensions": 1536,
                       "encoding_format": "float"}
    assert [v[0] for v in res.vectors] == [0.0, 1.0, 2.0]
    assert res.prompt_tokens == 42


def test_cliente_divide_em_lotes():
    n = embeddings.BATCH_SIZE + 5
    t = FakeTransport([_response(embeddings.BATCH_SIZE, tokens=1), _response(5, tokens=2)])
    res = embeddings.OpenAIEmbedder(api_key="k", transport=t).embed(["x"] * n)
    assert len(res.vectors) == n and res.prompt_tokens == 3 and len(t.calls) == 2


def test_cliente_rejeita_dimensao_errada():
    t = FakeTransport([_response(1, dims=3)])
    with pytest.raises(embeddings.EmbeddingError, match="Dimensão"):
        embeddings.OpenAIEmbedder(api_key="k", transport=t).embed(["a"])


def test_cliente_repete_em_429_e_desiste_em_400():
    retry = embeddings._HTTPStatus(429, "rate limit")
    t = FakeTransport([retry, _response(1)])
    sleeps = []
    embeddings.OpenAIEmbedder(api_key="k", transport=t, sleep=sleeps.append).embed(["a"])
    assert sleeps == [1] and len(t.calls) == 2

    t = FakeTransport([embeddings._HTTPStatus(400, "bad request")])
    with pytest.raises(embeddings.EmbeddingError, match="HTTP 400"):
        embeddings.OpenAIEmbedder(api_key="k", transport=t, sleep=lambda s: None).embed(["a"])
    assert len(t.calls) == 1


def test_cliente_nao_repete_quando_falta_credito():
    body = '{"error": {"type": "insufficient_quota", "code": "credit_balance_exhausted"}}'
    t = FakeTransport([embeddings._HTTPStatus(429, body)])
    sleeps = []
    with pytest.raises(embeddings.EmbeddingError, match="insufficient_quota"):
        embeddings.OpenAIEmbedder(api_key="k", transport=t, sleep=sleeps.append).embed(["a"])
    assert len(t.calls) == 1 and sleeps == []


def test_cliente_exige_chave(monkeypatch):
    for var in embeddings.KEY_VARS:
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(embeddings.EmbeddingError, match="Chave da OpenAI ausente"):
        embeddings.OpenAIEmbedder()


def test_chave_do_env_alternativo(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API", "sk-alt")
    assert embeddings.api_key_from_env() == "sk-alt"


def test_estimativa_de_custo():
    assert embeddings.estimate_tokens("abc") == 1
    assert embeddings.estimate_cost_usd(1_000_000) == pytest.approx(embeddings.PRICE_USD_PER_1M_TOKENS)


def test_fontes_originais_nao_sao_alteradas(sources):
    catalog, rules = sources
    build_documents(catalog, rules)
    assert json.loads(CATALOG_PATH.read_text(encoding="utf-8")) == catalog
    assert json.loads(RULES_PATH.read_text(encoding="utf-8")) == rules
