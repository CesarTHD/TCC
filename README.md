# TCC NL2SQL — Dataset experimental (PostgreSQL)

Banco de dados relacional **sintético, determinístico e documentado** usado como caso
experimental do TCC *"Arquitetura de Agentes de Inteligência Artificial para Consulta e
Análise de Dados Estruturados em Linguagem Natural"*.

O banco é o **mesmo** para todas as configurações avaliadas (NL2SQL direto, NL2SQL com
recuperação de contexto e arquitetura completa com agentes). Ele não é o produto do TCC.

| item | valor |
|---|---|
| SGBD | PostgreSQL 16 (Docker) |
| banco / schema | `tcc_nl2sql` / `dataset` |
| tabelas | `categorias`, `produtos`, `clientes`, `vendedores`, `pedidos`, `itens_pedido` |
| seed | `42` |
| data de referência ("hoje") | `2026-09-30` |
| período dos pedidos | 2023-01-01 a 2026-09-30 |
| role para os experimentos | `nl2sql_readonly` (somente SELECT) |

## Estrutura

```
tcc-nl2sql/
├── docker-compose.yml        # PostgreSQL + n8n
├── .env.example              # variáveis (copiar para .env)
├── docker/initdb/
│   ├── 01_init.sql           # init automático: schema dataset + role nl2sql_readonly
│   └── 02_experiments.sql    # init automático: banco tcc_experiments + role experiment_writer
├── database/
│   ├── schema.sql            # schema, constraints, índices, comentários
│   ├── roles.sql             # role nl2sql_readonly (+ grants.sql)
│   ├── grants.sql            # privilégios somente leitura
│   ├── reset.sql             # recria o schema vazio
│   ├── validation.sql        # estatísticas + verificações de integridade
│   ├── checksums.sql         # MD5 do conteúdo (reprodutibilidade)
│   └── experiments/          # banco de registro das execuções (database.sql, schema.sql)
├── seed/
│   ├── generator.py          # gerador determinístico (função pura)
│   ├── reference_data.py     # listas fixas e parâmetros das distribuições
│   ├── seed.py               # carga no banco (COPY)
│   ├── stats.py              # gera docs/dataset_statistics.md
│   ├── db.py                 # conexão via .env
│   └── requirements.txt
├── metadata/
│   ├── schema_catalog.json   # catálogo semântico (contexto para RAG)
│   └── business_rules.json   # regras de negócio R01–R12
├── tests/                    # pytest: gerador + banco + role read-only + catálogo + registro
├── web/                      # interface web (Next.js) — ver web/README.md
└── docs/
    ├── database.md           # modelo, constraints, índices, segurança
    ├── data_generation.md    # como os dados são gerados
    └── dataset_statistics.md # estatísticas reais (gerado por stats.py)
```

## 1. Requisitos

- Docker com Docker Compose v2 (`docker compose ...`)
- Python 3.10+ (testado com 3.14) para o seed, testes e estatísticas
- Opcional: cliente `psql` local (os comandos abaixo usam o `psql` de dentro do container)

## 2. Configurar o `.env`

```bash
cp .env.example .env        # PowerShell: Copy-Item .env.example .env
```

Edite `.env` e troque as senhas `POSTGRES_PASSWORD` e `NL2SQL_READONLY_PASSWORD`.
O `.env` está no `.gitignore` e não deve ser versionado. Se a porta 5432 já estiver em uso,
altere `POSTGRES_PORT`. Os scripts Python leem esse mesmo arquivo.

## 3. Iniciar o PostgreSQL

```bash
docker compose up -d
docker compose ps           # aguarde o status "healthy"
```

## 4. Criar o schema

Automático: na **primeira** inicialização (volume vazio), o container executa
`docker/initdb/01_init.sql`, que roda `database/schema.sql` e `database/roles.sql`
(cria o schema `dataset`, as tabelas e a role `nl2sql_readonly`).

Conferir:

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt dataset.*"'
```

Manualmente (por exemplo, em um PostgreSQL fora do Docker), conectado como administrador:

```bash
psql -h localhost -U tcc_admin -d tcc_nl2sql -f database/schema.sql
NL2SQL_READONLY_PASSWORD=... psql -h localhost -U tcc_admin -d tcc_nl2sql -f database/roles.sql
```

## 5. Gerar os dados (seed)

```bash
python -m venv .venv
# Linux/macOS:  source .venv/bin/activate
# Windows:      .venv\Scripts\activate      (ou use .venv\Scripts\python diretamente)
pip install -r seed/requirements.txt

python seed/seed.py
```

O seed gera o dataset em memória (seed 42), insere tudo em uma única transação e imprime
os checksums. Se as tabelas já tiverem dados ele se recusa a continuar; use `--reset`.

## 6. Validar

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /database/validation.sql'
```

A parte B lista as verificações de integridade; todas devem ter `ocorrencias = 0`. O script
termina com `VALIDAÇÃO OK` ou falha com erro (exit code ≠ 0).

Testes automatizados (gerador, conteúdo do banco, `validation.sql`, role read-only, catálogo):

```bash
python -m pytest tests -v
```

Os testes de banco são pulados automaticamente se o banco não estiver acessível.

Estatísticas reais (reescreve `docs/dataset_statistics.md`):

```bash
python seed/stats.py
```

## 7. Resetar

| objetivo | comando |
|---|---|
| refazer apenas os dados | `python seed/seed.py --reset` |
| recriar o schema vazio e popular | `docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /database/reset.sql'` e depois `python seed/seed.py` |
| apagar tudo (volume, roles) e recomeçar | `docker compose down -v`, `docker compose up -d` e `python seed/seed.py` |

## 8. Conectar ao banco

| parâmetro | valor |
|---|---|
| host | `localhost` (de outro container na mesma rede do Compose: `db`) |
| porta | `POSTGRES_PORT` (padrão 5432) |
| banco | `tcc_nl2sql` |
| administrador | `POSTGRES_USER` / `POSTGRES_PASSWORD` |
| experimentos | `nl2sql_readonly` / `NL2SQL_READONLY_PASSWORD` |

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
```

## 9. Usar a role `nl2sql_readonly`

É a credencial que o n8n usará para executar o SQL gerado pelo LLM. Ela:

- possui `CONNECT` no banco, `USAGE` no schema `dataset` e `SELECT` em todas as tabelas;
- **não** pode INSERT/UPDATE/DELETE/TRUNCATE/DROP/ALTER/CREATE (nem tabelas temporárias);
- tem `search_path = dataset` (o SQL pode usar `pedidos` em vez de `dataset.pedidos`);
- tem `default_transaction_read_only = on` e `statement_timeout = 30s`.

```bash
docker compose exec db psql -U nl2sql_readonly -d tcc_nl2sql -c "SELECT count(*) FROM pedidos"
docker compose exec db psql -U nl2sql_readonly -d tcc_nl2sql -c "DELETE FROM pedidos"   # deve falhar
```

(Dentro do container o socket local não pede senha; conexões TCP, como as do n8n, usam
`NL2SQL_READONLY_PASSWORD`.) Se trocar a senha no `.env` depois da primeira inicialização,
reaplique com:

```bash
docker compose up -d   # recria o container com a nova variável
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /database/roles.sql'
```

## 10. Verificar a reprodutibilidade

```bash
python seed/seed.py --checksums
```

Os MD5 impressos devem ser idênticos aos da seção 16 de `docs/dataset_statistics.md`. Além
disso, o teste `test_conteudo_do_banco_igual_ao_gerador` compara linha a linha o conteúdo do
banco com a saída do gerador, e `test_determinismo` gera o dataset duas vezes e compara o digest.
Para repetir o ciclo completo: `docker compose down -v`, `docker compose up -d`,
`python seed/seed.py` e compare os checksums.

## 11. Registro dos experimentos (`tcc_experiments`)

Cada requisição feita às arquiteturas pela interface web (rota `/api/chat`) pode ser gravada
no banco **`tcc_experiments`**, separado do dataset, no mesmo container:

| | Dataset (`tcc_nl2sql`) | Registro (`tcc_experiments`) |
|---|---|---|
| Role da aplicação | `nl2sql_readonly` (n8n) — só `SELECT` | `experiment_writer` (interface web) — `SELECT` + `INSERT` |
| Acesso cruzado | `nl2sql_readonly` **não conecta** em `tcc_experiments` | `experiment_writer` **não lê** o schema `dataset` |

Assim, nenhuma arquitetura consegue ler perguntas, SQL ou resultados anteriores, e o registro é
*append-only* (a aplicação não altera nem apaga linhas).

**Volume novo:** `docker/initdb/02_experiments.sql` cria tudo automaticamente.
**Volume já existente** (aplicar uma vez; é idempotente):

```bash
# 1. defina EXPERIMENT_WRITER_PASSWORD no .env
docker compose up -d db          # recria o container com a nova variável (o volume é mantido)
docker exec tcc-nl2sql-db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/02_experiments.sql'
```

Depois configure `EXPERIMENT_DATABASE_URL` em `web/.env.local` (ver `web/README.md`).

Estrutura (schema `eval`, detalhes em `database/experiments/schema.sql`):

| Objeto | Conteúdo |
|---|---|
| `eval.experiment` | uma rodada de avaliação: `label`, `description`, `config` (modelo, prompts, checksum do dataset…) |
| `eval.run` | uma linha por requisição: pergunta, esclarecimento respondido, status, SQL gerado, erro, colunas/linhas (até 500), hash do resultado completo, tempo informado pela arquitetura, latência medida pela rota, tentativas, contexto usado, metadata e resposta completa |
| `eval.operation_outcome` | última tentativa de cada mensagem (desconsidera reenvios) |
| `eval.conversation_outcome` | estado final de cada conversa, com rodadas de esclarecimento e latência total |
| `eval.architecture_summary` | por experimento e arquitetura: concluídas, erros, erros de integração, média de esclarecimentos, medianas de tempo |

Criar uma rodada e consultar os resultados:

```bash
docker exec -it tcc-nl2sql-db psql -U tcc_admin -d tcc_experiments
```

```sql
INSERT INTO eval.experiment (label, description, config)
VALUES ('rodada-1', 'Avaliação inicial das 3 arquiteturas',
        '{"modelo": "...", "temperatura": 0, "dataset_seed": 42}')
RETURNING id;

SELECT * FROM eval.architecture_summary WHERE experiment_id = '<id>';

SELECT question_id, architecture, final_status, generated_sql, row_count
FROM eval.conversation_outcome
WHERE experiment_id = '<id>'
ORDER BY question_id, architecture;
```

> Para avaliar, use **uma conversa por pergunta**. Linhas sem `experiment_id` são uso livre da
> interface. Para remover execuções de teste, use a role administrativa
> (`DELETE FROM eval.run WHERE experiment_id = ...`).

## Documentação

- [web/README.md](web/README.md): interface web experimental (chat com as arquiteturas no n8n)
- [web/docs/n8n-integration.md](web/docs/n8n-integration.md): contrato HTTP que os workflows do n8n devem seguir
- [docs/database.md](docs/database.md): modelo, regras financeiras e temporais, constraints, índices, segurança
- [docs/data_generation.md](docs/data_generation.md): algoritmo e distribuições do gerador
- [docs/dataset_statistics.md](docs/dataset_statistics.md): estatísticas reais do dataset
- [metadata/schema_catalog.json](metadata/schema_catalog.json) e [metadata/business_rules.json](metadata/business_rules.json): contexto semântico para a arquitetura

> `docs/dataset_statistics.md` contém resultados agregados; ele não deve ser usado como
> contexto das arquiteturas avaliadas. O contexto permitido é o de `metadata/`.
