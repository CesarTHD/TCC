# Indexação semântica dos metadados (arquitetura B)

Este documento descreve como `metadata/schema_catalog.json` e `metadata/business_rules.json` são
transformados em documentos semânticos, vetorizados e armazenados no schema `rag` do banco
`tcc_nl2sql`. A recuperação contextual e a integração com o n8n **ainda não** estão implementadas.
Esta etapa só produz o índice.

## 1. Visão geral

```
metadata/schema_catalog.json ─┐
                              ├─► rag/documents.py ─► 24 documentos ─► rag/embeddings.py ─► rag.documents
metadata/business_rules.json ─┘   (função pura)       (texto + JSONB)   (OpenAI, só --index)   (pgvector)
```

| item | valor |
|---|---|
| modelo de embeddings | `text-embedding-3-small` (OpenAI) |
| dimensões | 1536 (dimensão nativa, enviada explicitamente em `dimensions`) |
| formato | `encoding_format = float`; armazenado como `vector(1536)` (float32) |
| versão do construtor de documentos | `BUILDER_VERSION = "1"` (`rag/documents.py`) |
| texto vetorizado | campo `content` do documento, sem pré-processamento |
| índice vetorial (HNSW/IVFFlat) | não criado: com 24 vetores, a busca exata é trivial |

## 2. Documentos

Um documento por unidade semântica, para que a recuperação devolva blocos completos e
autoexplicativos:

| tipo | `doc_id` | qtd. | conteúdo |
|---|---|---|---|
| `visao_geral` | `visao_geral:dataset` | 1 | banco, schema, SGBD, descrição, data de referência, período, convenções, lista de tabelas e de regras |
| `tabela` | `tabela:<nome>` | 6 | descrição, granularidade, termos, PK, regras da tabela; cada coluna com tipo, NULL/NOT NULL, PK, UNIQUE, FK, descrição, termos, valores possíveis (com descrição) e regras; relacionamentos da tabela |
| `relacionamento` | `relacionamento:<de>-><para>` | 5 | colunas de origem e destino, cardinalidade, descrição, condição de junção e descrição/termos das duas tabelas |
| `regra` | `regra:<id>` | 12 | id, nome, termos, definição, definição SQL, tabelas, colunas e observações |

**Total: 24 documentos.**

**Fidelidade aos metadados.** Todo o texto vem de campos dos dois arquivos JSON. Os únicos
textos fixos são os rótulos (`Tabela:`, `Colunas:`, `Valores possíveis:` ...), a qualificação
com o schema (`dataset.pedidos`) e a condição de junção `a = b`, derivada de `de`/`para`. Os
nomes das regras citados nos documentos de tabela (ex.: `R07 (Preço praticado x preço atual)`)
vêm de `business_rules.json`. Os testes verificam que cada campo de cada coluna, valor, termo e
regra aparece no documento correspondente e que nenhum valor categórico fora do catálogo
aparece nos textos.

Os metadados JSONB de cada documento guardam, para filtros e rastreabilidade: `doc_type`,
`source`, `schema`, `tables`, `columns`, `rule_ids`, `terms`, PK/FKs e relacionamentos (tabelas),
`from`/`to`/`cardinality` (relacionamentos), `builder_version`, `catalog_version`,
`rules_version`, `schema_catalog_sha256` e `business_rules_sha256`.

Para inspecionar os textos gerados sem acessar a API:

```bash
python -m rag.indexer --dry-run --export documentos_rag.jsonl
```

## 3. Tabelas

As tabelas são criadas por `--index` (`CREATE ... IF NOT EXISTS`). O DDL está em `rag/store.py`.

**`rag.documents`** (uma linha por documento)

| coluna | conteúdo |
|---|---|
| `doc_id` (PK) | identificador estável (ver tabela acima) |
| `doc_type` | `visao_geral`, `tabela`, `relacionamento` ou `regra` |
| `title`, `content` | título e texto vetorizado |
| `content_sha256` | SHA-256 do texto em UTF-8 |
| `metadata` | JSONB descrito na seção 2 |
| `embedding` | `vector(1536)` |
| `embedding_model`, `embedding_dimensions` | modelo e dimensão usados para gerar o vetor |
| `embedding_sha256` | SHA-256 do vetor como 1536 float32 little-endian |
| `embedded_at`, `updated_at` | data do último embedding e da última alteração |

**`rag.index_runs`** (uma linha por execução de `--index`): modelo, dimensões, versão do
construtor, `corpus_sha256`, hashes dos dois arquivos de metadados, contagens (documentos,
vetorizados, só metadados, inalterados, removidos), `prompt_tokens` informados pela API e ids dos
documentos vetorizados e removidos.

A role `nl2sql_readonly` (usada para executar o SQL gerado) não tem acesso ao schema `rag`.

**Leitura pelo workflow B.** A busca vetorial no n8n usa a role `rag_reader`
([database/rag_reader.sql](../database/rag_reader.sql)): `SELECT` somente em `rag.documents`,
sem acesso a `dataset`, a `rag.index_runs` ou a `tcc_experiments`, com
`default_transaction_read_only = on` e `statement_timeout = 10s`. A senha fica em
`RAG_READER_PASSWORD` no `.env`. Criar ou atualizar a role (idempotente, depois do primeiro `--index`):

```bash
docker exec -e RAG_READER_PASSWORD=<senha do .env> tcc-nl2sql-db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /database/rag_reader.sql'
```

No n8n, o nó "Buscar metadados pgvector" usa a credencial `Postgres rag_reader` (host `db`,
banco `tcc_nl2sql`). A credencial `Postgres account` (`nl2sql_readonly`) fica só para executar o
SQL gerado.

## 4. Indexação incremental e idempotente

Para cada documento gerado, `store.plan()` compara com a linha em `rag.documents`:

| situação | ação | chama a API? |
|---|---|---|
| doc não existe no banco | INSERT com embedding | sim |
| `content_sha256`, modelo ou dimensão diferente | UPDATE com novo embedding | sim |
| texto igual; metadados, título ou tipo diferentes | UPDATE sem embedding | não |
| tudo igual | nada | não |
| doc no banco que não é mais gerado | DELETE | não |

- Os embeddings dos documentos novos/alterados são pedidos em uma única requisição (lotes de 64).
- Tudo ocorre em **uma transação**. Se a API falhar, nada é gravado.
- `pg_advisory_xact_lock` impede duas indexações simultâneas.
- Sem documentos a vetorizar, a chave da OpenAI não é lida e a API não é chamada.
- Alterar uma regra muda o texto só dessa regra (e, se o **nome** mudar, dos documentos que o
  citam). Os demais documentos têm apenas os metadados atualizados, porque o hash do arquivo de
  origem muda.

## 5. Comandos

Executar na raiz do projeto, com o `.venv` ativo (ou `.venv\Scripts\python` no Windows):

```bash
python -m rag.indexer --dry-run                 # documentos, plano, tokens e custo estimados (sem API, sem escrita)
python -m rag.indexer --dry-run --export docs.jsonl
python -m rag.indexer --index                   # cria as tabelas se preciso e vetoriza só o que mudou
python -m rag.indexer --status                  # estado do índice; exit code 2 se desatualizado
```

Credenciais lidas do `.env` (mesmo arquivo do seed): `POSTGRES_*` para o banco (role
administrativa) e `OPENAI_API_KEY` (ou `OPENAI_API`) para a OpenAI. A chave nunca é impressa nem
gravada. Não há dependências novas: o cliente HTTP usa só a biblioteca padrão do Python.

## 6. Custo

Preço de tabela do `text-embedding-3-small`: US$ 0,02 por 1 milhão de tokens (confira em
<https://openai.com/api/pricing> antes de executar).

| | tokens | custo |
|---|---|---|
| corpus completo (24 docs, ~25 mil caracteres) | ≤ ~8,6 mil (estimativa conservadora: 3 bytes UTF-8/token) | ≤ ~US$ 0,00017 |

A contagem real é a informada pela API, registrada em `rag.index_runs.prompt_tokens`.
Reexecuções sem mudanças custam zero.

## 7. Reprodutibilidade

Registre no trabalho, a partir de `--status` ou de `rag.index_runs`:

| hash | o que identifica |
|---|---|
| `schema_catalog_sha256`, `business_rules_sha256` | conteúdo dos metadados (JSON canônico: chaves ordenadas, sem espaços, independente de fim de linha) |
| `content_sha256` | texto exato de cada documento enviado ao modelo |
| `corpus_sha256` | conjunto completo: SHA-256 das linhas `doc_id<TAB>content_sha256` ordenadas por `doc_id` e unidas por `\n` |
| `embedding_sha256` | vetor armazenado de cada documento |

Valores da versão atual dos metadados (`BUILDER_VERSION = "1"`):

| item | SHA-256 |
|---|---|
| `schema_catalog.json` | `cc64d0e88641c81a5dd6947dce39af4d003dfdfeda51d3d743f5e7474382be3f` |
| `business_rules.json` | `7d894462a1ad56761319d515364ea54f8e837a13485c94b93f82ff1c776ccd40` |
| corpus (24 docs) | `50ef061ae473c81426aaa96bed21327ed310f41d4cd507ac437246765ca2f561` |

**Os textos são determinísticos, os embeddings não necessariamente.** A mesma entrada gera
sempre os mesmos documentos e `content_sha256`, mas a API da OpenAI não garante vetores
idênticos bit a bit entre chamadas (variações numéricas mínimas). Para repetir os experimentos
com exatamente o mesmo índice, use os vetores já armazenados (eles estão no backup do banco, ver
README seção 12) e confira os `embedding_sha256`. Reindexar do zero produz vetores
equivalentes, mas não necessariamente com o mesmo `embedding_sha256`.

**Alterar o formato dos textos** (em `rag/documents.py`) exige incrementar `BUILDER_VERSION`. Os
textos alterados mudam o `content_sha256` e são revetorizados no próximo `--index`.

**Trocar de modelo ou dimensão** exige alterar `MODEL`/`DIMENSIONS` em `rag/embeddings.py` e o
tipo `vector(N)` da tabela (a coluna tem dimensão fixa). Com a mesma dimensão, a troca de modelo
é detectada e todos os documentos são revetorizados.

## 8. Testes

```bash
python -m pytest tests/test_rag_documents.py tests/test_rag_store.py -v
```

- `test_rag_documents.py` (sem banco e sem rede): quantidade e tipos, determinismo, hashes,
  cobertura completa dos metadados, ausência de valores inventados, efeito de alterações nos
  hashes, plano incremental, float32/hash dos vetores e o cliente da API com transporte falso
  (formato da requisição, lotes, dimensão errada, novas tentativas em 429, erro em 400, chave
  ausente).
- `test_rag_store.py` (pulado sem banco): indexação com embedder falso em um schema temporário,
  dentro de uma transação desfeita ao final. O schema `rag` real não é tocado. Cobre primeira
  indexação, idempotência (zero chamadas na segunda execução), revetorização só do documento
  alterado, remoção, integridade de textos/hashes/vetores gravados, `status`, troca de modelo e
  falha da API sem gravação parcial.

Nenhum teste chama a API da OpenAI.
