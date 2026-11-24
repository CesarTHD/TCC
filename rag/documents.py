"""Transforma metadata/schema_catalog.json e metadata/business_rules.json em documentos semânticos.

Função pura e determinística: a mesma entrada produz sempre os mesmos textos e hashes.
Todo o texto é montado a partir de campos dos dois arquivos; nenhum conteúdo é inventado.
Os únicos textos fixos são os rótulos dos campos ("Tabela:", "Colunas:" ...) e a forma
"a = b" da condição de junção, derivada mecanicamente de "de"/"para" do relacionamento.

Tipos de documento (um embedding por documento):
    visao_geral     banco, schema, período, data de referência, convenções e lista de tabelas
    tabela          uma tabela com todas as colunas, tipos, restrições, termos, valores e regras
    relacionamento  uma chave estrangeira, com cardinalidade, descrição e condição de junção
    regra           uma regra de negócio completa (definição, SQL, tabelas, colunas, observações)

Alterar o formato dos textos exige incrementar BUILDER_VERSION (registrado nos metadados e
em rag.index_runs). Como o hash é calculado sobre o texto, documentos cujo texto mudou são
reindexados automaticamente.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "metadata" / "schema_catalog.json"
RULES_PATH = ROOT / "metadata" / "business_rules.json"

BUILDER_VERSION = "1"
DOC_TYPES = ("visao_geral", "tabela", "relacionamento", "regra")


@dataclass(frozen=True)
class Document:
    doc_id: str
    doc_type: str
    title: str
    content: str
    metadata: dict = field(hash=False)

    @property
    def content_sha256(self) -> str:
        return sha256_text(self.content)

    @property
    def metadata_json(self) -> str:
        return canonical_json(self.metadata)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def source_sha256(obj) -> str:
    """Hash do conteúdo JSON em forma canônica (independe de espaços e de fim de linha)."""
    return sha256_text(canonical_json(obj))


def load_sources(catalog_path: Path = CATALOG_PATH, rules_path: Path = RULES_PATH) -> tuple[dict, dict]:
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    rules = json.loads(Path(rules_path).read_text(encoding="utf-8"))
    return catalog, rules


def corpus_sha256(docs: list[Document]) -> str:
    """Identifica o conjunto completo de documentos (ids + hashes dos textos)."""
    return sha256_text("\n".join(f"{d.doc_id}\t{d.content_sha256}" for d in sorted(docs, key=lambda d: d.doc_id)))


# --------------------------------------------------------------------------- helpers de texto

def _list(values) -> str:
    return ", ".join(str(v) for v in values)


def _qualified(schema: str, ref: str) -> str:
    """'pedidos.cliente_id' -> 'dataset.pedidos.cliente_id'."""
    return f"{schema}.{ref}"


def _column_line(schema: str, col: dict, rule_names: dict[str, str]) -> str:
    attrs = [col["tipo"], "NULL" if col.get("nulo") else "NOT NULL"]
    if col.get("pk"):
        attrs.append("PK")
    if col.get("unico"):
        attrs.append("UNIQUE")
    if col.get("fk"):
        attrs.append(f"FK -> {schema}.{col['fk']['tabela']}.{col['fk']['coluna']}")
    parts = [f"- {col['nome']} ({', '.join(attrs)}): {col['descricao']}"]
    if col.get("termos"):
        parts.append(f"Termos: {_list(col['termos'])}.")
    if col.get("valores_possiveis"):
        vals = []
        for v in col["valores_possiveis"]:
            vals.append(f"'{v['valor']}' ({v['descricao']})" if v.get("descricao") else f"'{v['valor']}'")
        parts.append(f"Valores possíveis: {'; '.join(vals)}.")
    if col.get("regras"):
        parts.append(f"Regras: {_list(_rule_label(r, rule_names) for r in col['regras'])}.")
    return " ".join(parts)


def _rule_label(rule_id: str, rule_names: dict[str, str]) -> str:
    return f"{rule_id} ({rule_names[rule_id]})" if rule_id in rule_names else rule_id


def _relationship_id(rel: dict) -> str:
    return f"relacionamento:{rel['de']}->{rel['para']}"


# --------------------------------------------------------------------------- documentos

def _overview(catalog: dict, rules: dict) -> Document:
    schema = catalog["schema"]
    lines = [
        f"Banco: {catalog['banco']}",
        f"Schema: {schema}",
        f"SGBD: {catalog['sgbd']}",
        f"Descrição: {catalog['descricao']}",
        f"Data de referência ('hoje'): {catalog['data_referencia']}",
        f"Período dos pedidos: {catalog['periodo_pedidos']['inicio']} a {catalog['periodo_pedidos']['fim']}",
        "Convenções:",
        *(f"- {c}" for c in catalog["convencoes"]),
        "Tabelas:",
        *(f"- {schema}.{t['nome']}: {t['descricao']} {t['granularidade']}" for t in catalog["tabelas"]),
        f"Regras de negócio: {rules['descricao']}",
        *(f"- {r['id']}: {r['nome']}" for r in rules["regras"]),
    ]
    return Document(
        doc_id="visao_geral:dataset",
        doc_type="visao_geral",
        title=f"Visão geral do schema {schema}",
        content="\n".join(lines),
        metadata={
            "doc_type": "visao_geral",
            "source": ["schema_catalog.json", "business_rules.json"],
            "schema": schema,
            "tables": [t["nome"] for t in catalog["tabelas"]],
            "rule_ids": [r["id"] for r in rules["regras"]],
        },
    )


def _table(catalog: dict, table: dict, rule_names: dict[str, str]) -> Document:
    schema = catalog["schema"]
    name = table["nome"]
    rels = [r for r in catalog["relacionamentos"]
            if r["de"].split(".")[0] == name or r["para"].split(".")[0] == name]
    table_rules = list(table.get("regras", []))
    column_rules = sorted({r for c in table["colunas"] for r in c.get("regras", [])})
    lines = [
        f"Tabela: {schema}.{name}",
        f"Descrição: {table['descricao']}",
        f"Granularidade: {table['granularidade']}",
        f"Termos de negócio: {_list(table['termos'])}",
        f"Chave primária: {_list(table['chave_primaria'])}",
    ]
    if table_rules:
        lines.append(f"Regras de negócio da tabela: {_list(_rule_label(r, rule_names) for r in table_rules)}")
    lines.append("Colunas:")
    lines.extend(_column_line(schema, c, rule_names) for c in table["colunas"])
    if rels:
        lines.append("Relacionamentos:")
        lines.extend(
            f"- {_qualified(schema, r['de'])} -> {_qualified(schema, r['para'])} ({r['cardinalidade']}): {r['descricao']}"
            for r in rels
        )
    return Document(
        doc_id=f"tabela:{name}",
        doc_type="tabela",
        title=f"Tabela {schema}.{name}",
        content="\n".join(lines),
        metadata={
            "doc_type": "tabela",
            "source": ["schema_catalog.json"],
            "schema": schema,
            "table": name,
            "tables": [name],
            "columns": [f"{name}.{c['nome']}" for c in table["colunas"]],
            "primary_key": table["chave_primaria"],
            "foreign_keys": [{"column": f"{name}.{c['nome']}", "references": f"{c['fk']['tabela']}.{c['fk']['coluna']}"}
                             for c in table["colunas"] if c.get("fk")],
            "relationships": [_relationship_id(r) for r in rels],
            "rule_ids": sorted(set(table_rules) | set(column_rules)),
            "terms": table["termos"],
        },
    )


def _relationship(catalog: dict, rel: dict) -> Document:
    schema = catalog["schema"]
    tables = {t["nome"]: t for t in catalog["tabelas"]}
    src_table, src_col = rel["de"].split(".")
    dst_table, dst_col = rel["para"].split(".")
    lines = [
        f"Relacionamento: {_qualified(schema, rel['de'])} -> {_qualified(schema, rel['para'])}",
        f"Cardinalidade: {rel['cardinalidade']} ({src_table} -> {dst_table})",
        f"Descrição: {rel['descricao']}",
        f"Condição de junção: {_qualified(schema, rel['de'])} = {_qualified(schema, rel['para'])}",
    ]
    for tname in (src_table, dst_table):
        t = tables.get(tname)
        if t:
            lines.append(f"Tabela {schema}.{tname}: {t['descricao']} {t['granularidade']} Termos: {_list(t['termos'])}.")
    return Document(
        doc_id=_relationship_id(rel),
        doc_type="relacionamento",
        title=f"Relacionamento {rel['de']} -> {rel['para']}",
        content="\n".join(lines),
        metadata={
            "doc_type": "relacionamento",
            "source": ["schema_catalog.json"],
            "schema": schema,
            "from": rel["de"],
            "to": rel["para"],
            "cardinality": rel["cardinalidade"],
            "tables": [src_table, dst_table],
            "columns": [rel["de"], rel["para"]],
        },
    )


def _rule(catalog: dict, rule: dict) -> Document:
    lines = [
        f"Regra de negócio {rule['id']}: {rule['nome']}",
        f"Termos: {_list(rule['termos'])}",
        f"Definição: {rule['definicao']}",
        f"Definição SQL: {rule['definicao_sql']}",
        f"Tabelas: {_list(rule['tabelas'])}",
        f"Colunas: {_list(rule['colunas'])}",
    ]
    if rule.get("observacoes"):
        lines.append(f"Observações: {rule['observacoes']}")
    return Document(
        doc_id=f"regra:{rule['id']}",
        doc_type="regra",
        title=f"Regra {rule['id']} — {rule['nome']}",
        content="\n".join(lines),
        metadata={
            "doc_type": "regra",
            "source": ["business_rules.json"],
            "schema": catalog["schema"],
            "rule_id": rule["id"],
            "rule_ids": [rule["id"]],
            "tables": rule["tabelas"],
            "columns": rule["colunas"],
            "terms": rule["termos"],
        },
    )


def build_documents(catalog: dict, rules: dict) -> list[Document]:
    """Gera os documentos em ordem estável: visão geral, tabelas, relacionamentos, regras."""
    rule_names = {r["id"]: r["nome"] for r in rules["regras"]}
    sources = {"schema_catalog_sha256": source_sha256(catalog), "business_rules_sha256": source_sha256(rules)}
    docs = [_overview(catalog, rules)]
    docs += [_table(catalog, t, rule_names) for t in catalog["tabelas"]]
    docs += [_relationship(catalog, r) for r in catalog["relacionamentos"]]
    docs += [_rule(catalog, r) for r in rules["regras"]]
    ids = [d.doc_id for d in docs]
    if len(ids) != len(set(ids)):
        raise ValueError("doc_id duplicado nos metadados")
    for d in docs:
        d.metadata["builder_version"] = BUILDER_VERSION
        d.metadata["catalog_version"] = catalog.get("versao")
        d.metadata["rules_version"] = rules.get("versao")
        d.metadata.update(sources)
    return docs


def load_documents() -> list[Document]:
    return build_documents(*load_sources())
