# Banco de dados experimental

Este documento descreve o banco `tcc_nl2sql`, schema `dataset`, conforme implementado em
`database/schema.sql`. A descrição semântica, legível por máquina e pensada para recuperação
de contexto, está em `metadata/schema_catalog.json`. As regras de negócio estão em
`metadata/business_rules.json`.

## 1. Modelo

```
categorias (10)
    │ 1
    │
    │ N
produtos (222) ───────────┐
                          │ 1
                          │
                          │ N
clientes (2000) 1 ── N  pedidos (≈12 mil) 1 ── N  itens_pedido (≈33 mil)
                          │ N
                          │
                          │ 1
                     vendedores (25)
```

| relacionamento | cardinalidade | observação |
|---|---|---|
| `produtos.categoria_id → categorias.id` | N:1 | toda categoria tem produtos |
| `pedidos.cliente_id → clientes.id` | N:1 | há clientes sem pedidos |
| `pedidos.vendedor_id → vendedores.id` | N:1 | todo pedido tem vendedor, inclusive SITE/APP |
| `itens_pedido.pedido_id → pedidos.id` | N:1 | todo pedido tem ≥ 1 item |
| `itens_pedido.produto_id → produtos.id` | N:1 | um produto aparece no máximo 1 vez por pedido |

## 2. Tabelas

### categorias
| coluna | tipo | restrições | significado |
|---|---|---|---|
| id | integer | PK | identificador |
| nome | varchar(60) | NOT NULL, UNIQUE | nome da categoria |
| descricao | varchar(255) | NOT NULL | descrição |

### produtos
| coluna | tipo | restrições | significado |
|---|---|---|---|
| id | integer | PK | identificador |
| categoria_id | integer | NOT NULL, FK categorias | categoria |
| nome | varchar(120) | NOT NULL, UNIQUE | "<tipo de produto> <marca fictícia>" |
| descricao | varchar(255) | NOT NULL | marca e linha (econômica/intermediária/premium) |
| preco | numeric(12,2) | NOT NULL, > 0 | preço de tabela **atual** (em 2026-09-30) |
| ativo | boolean | NOT NULL | false = descontinuado |
| data_cadastro | date | NOT NULL, ≤ 2026-09-30 | entrada no catálogo |

### clientes
| coluna | tipo | restrições | significado |
|---|---|---|---|
| id | integer | PK | identificador |
| nome | varchar(120) | NOT NULL | nome fictício (pode haver homônimos) |
| email | varchar(160) | NOT NULL, UNIQUE | `...@example.com` |
| data_nascimento | date | NOT NULL, < data_cadastro | nascimento |
| data_cadastro | date | NOT NULL, ≤ 2026-09-30 | cadastro (pode ser anterior a 2023) |
| cidade | varchar(80) | NOT NULL | cidade |
| uf | char(2) | NOT NULL, CHECK 27 UFs | estado |
| segmento | varchar(10) | CHECK `PADRAO`/`PREMIUM` | programa de fidelidade |
| status | varchar(10) | CHECK `ATIVO`/`INATIVO` | situação cadastral, independente de compras |

### vendedores
| coluna | tipo | restrições | significado |
|---|---|---|---|
| id | integer | PK | identificador |
| nome | varchar(120) | NOT NULL | nome fictício |
| email | varchar(160) | NOT NULL, UNIQUE | `...@vendas.example.com` |
| data_admissao | date | NOT NULL, ≤ 2026-09-30 | admissão |
| data_desligamento | date | NULL, > data_admissao | desligamento (NULL se ativo) |
| regiao | varchar(12) | CHECK NORTE/NORDESTE/CENTRO-OESTE/SUDESTE/SUL | região de atuação |
| status | varchar(10) | CHECK `ATIVO`/`INATIVO`; INATIVO ⇔ data_desligamento preenchida | situação |

### pedidos
| coluna | tipo | restrições | significado |
|---|---|---|---|
| id | integer | PK | identificador (cronológico) |
| cliente_id | integer | NOT NULL, FK clientes | cliente |
| vendedor_id | integer | NOT NULL, FK vendedores | vendedor responsável |
| data_pedido | date | NOT NULL, 2023-01-01..2026-09-30 | data do pedido |
| status | varchar(10) | CHECK `CONCLUIDO`/`CANCELADO`/`PENDENTE` | situação |
| canal_venda | varchar(10) | CHECK `SITE`/`LOJA`/`APP`/`TELEFONE` | canal |
| valor_total | numeric(12,2) | NOT NULL, ≥ 0 | soma de `valor_total_item` |

### itens_pedido
| coluna | tipo | restrições | significado |
|---|---|---|---|
| id | integer | PK | identificador |
| pedido_id | integer | NOT NULL, FK pedidos | pedido |
| produto_id | integer | NOT NULL, FK produtos | produto |
| quantidade | integer | NOT NULL, > 0 | unidades |
| preco_unitario | numeric(12,2) | NOT NULL, > 0 | preço praticado na data do pedido |
| desconto | numeric(12,2) | NOT NULL, ≥ 0, ≤ quantidade × preco_unitario | desconto do item em R$ |
| valor_total_item | numeric(12,2) | NOT NULL, = quantidade × preco_unitario − desconto | valor líquido |

Restrição adicional: `UNIQUE (pedido_id, produto_id)`.

## 3. Regras financeiras

```
valor_total_item   = quantidade * preco_unitario - desconto          (CHECK no banco)
pedidos.valor_total = SUM(itens_pedido.valor_total_item) do pedido   (verificado em validation.sql e nos testes)
```

- `desconto` é um valor absoluto em R$ por item (não percentual). Pedidos não têm desconto próprio.
- `preco_unitario` é o preço histórico, gravado no momento da venda. `produtos.preco` é o preço
  atual; os dois diferem porque os preços sobem com o tempo (regra R07).
- Pedidos `CANCELADO` e `PENDENTE` permanecem armazenados com itens e `valor_total` (o valor que
  a transação teria). **Faturamento, vendas, quantidade vendida e ticket médio consideram
  apenas `CONCLUIDO`** (regras R01–R06, R12).
- Faturamento por produto/categoria usa `SUM(itens_pedido.valor_total_item)`, e não
  `pedidos.valor_total`, para não contar o mesmo pedido mais de uma vez após o JOIN (R06).

A consistência `pedidos.valor_total = soma dos itens` **não** é imposta por trigger. O dataset
é estático (somente leitura nos experimentos), então a regra é garantida pelo gerador e
verificada por `validation.sql` e pelos testes. Isso mantém o schema simples.

## 4. Regras temporais

| regra | garantia |
|---|---|
| `data_pedido` entre 2023-01-01 e 2026-09-30 | CHECK + validação |
| `data_pedido ≥ clientes.data_cadastro` | gerador + validação |
| `data_admissao ≤ data_pedido ≤ data_desligamento` do vendedor | gerador + validação |
| produto vendido somente a partir de `produtos.data_cadastro` | gerador + validação |
| nenhuma data posterior a 2026-09-30 | CHECK + validação |
| cliente com ≥ 18 anos no cadastro | gerador + validação |
| pedidos `PENDENTE` somente nos últimos 45 dias antes da referência | gerador + teste |

As regras que envolvem duas tabelas não são CHECK constraints, porque o PostgreSQL não
permite subconsultas em CHECK e triggers aumentariam a complexidade. Elas são verificadas
por `validation.sql`.

**Data de referência.** "Hoje" é sempre 2026-09-30 (regra R09). Nenhum valor do dataset
depende de `CURRENT_DATE`/`NOW()`. O SQL avaliado também deve usar `DATE '2026-09-30'`
para expressões relativas.

## 5. Índices

PKs e UNIQUE já criam índices implicitamente (inclusive `itens_pedido (pedido_id, produto_id)`,
que atende JOINs por `pedido_id`). Índices criados explicitamente:

| índice | justificativa |
|---|---|
| `idx_produtos_categoria_id` | FK; JOIN/agrupamento por categoria |
| `idx_pedidos_cliente_id` | FK; JOIN com clientes, consultas por cliente e de ausência (`NOT EXISTS`) |
| `idx_pedidos_vendedor_id` | FK; JOIN/agrupamento por vendedor |
| `idx_pedidos_data_pedido` | filtros de período, a condição mais comum em análises temporais |
| `idx_itens_pedido_produto_id` | FK; vendas por produto/categoria, produtos sem venda |

Não foi criado índice em `pedidos.status`: com 3 valores e ~93% `CONCLUIDO`, ele tem baixa
seletividade e o planner não o usaria para o filtro mais comum. Com ~12 mil pedidos, varreduras
sequenciais são baratas. Não houve outras otimizações, para não otimizar prematuramente.

## 6. Segurança

| role | uso | privilégios |
|---|---|---|
| `POSTGRES_USER` (ex.: `tcc_admin`) | inicialização, seed, manutenção | superusuário do container, dono do schema |
| `nl2sql_readonly` | execução do SQL gerado pelo LLM (n8n) | `CONNECT`, `USAGE` em `dataset`, `SELECT` nas tabelas |

Configuração de `nl2sql_readonly` (`database/roles.sql` e `database/grants.sql`):

- `LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS`, limite de 20 conexões;
- `search_path = dataset`, `default_transaction_read_only = on`, `statement_timeout = 30s`;
- `REVOKE CREATE ON SCHEMA public` e `REVOKE CREATE, TEMPORARY ON DATABASE` de `PUBLIC`;
- `ALTER DEFAULT PRIVILEGES` garante somente SELECT em tabelas criadas no futuro no schema.

`default_transaction_read_only` é só uma camada adicional, porque a sessão pode desligá-lo. A
proteção efetiva é a ausência de privilégios de escrita/DDL. O teste
`test_readonly_sem_privilegio_mesmo_fora_de_transacao_readonly` desliga o modo read-only e
confirma que INSERT, UPDATE, DELETE, TRUNCATE, DROP, ALTER e CREATE continuam negados.

As senhas vêm de variáveis de ambiente (`.env`, fora do versionamento).

## 7. Extensão pgvector e schema `rag`

| item | valor |
|---|---|
| imagem Docker | `pgvector/pgvector:pg16-trixie` (Debian 13, glibc 2.41) |
| PostgreSQL | 16 (16.16 na instalação) |
| extensão | `vector` 0.8.7, no schema `public` de `tcc_nl2sql` |
| schema | `rag`, dono `POSTGRES_USER` |

O schema `rag` guarda os metadados vetoriais da arquitetura B (recuperação semântica sobre
`metadata/schema_catalog.json` e `metadata/business_rules.json`). Ele é separado de `dataset`
para que os dados avaliados não mudem e para que o contexto do RAG possa ser recriado sem tocar
no dataset. A role `nl2sql_readonly` não tem `USAGE` em `rag`, então o SQL gerado pelas
arquiteturas não lê nem altera os embeddings. As tabelas `rag.documents` e `rag.index_runs`
são criadas por `python -m rag.indexer --index` e descritas em `docs/rag_indexing.md`.

A variante `-trixie` usa a mesma glibc da imagem `postgres:16` que criou o volume, então a
versão de collation `en_US.utf8` registrada em `pg_database.datcollversion` (2.41) continua igual
à do sistema. Procedimento de instalação e backup/restauração: README, seções 3 e 12.

## 8. Dados pessoais

Todos os dados são fictícios: nomes são combinações aleatórias de listas fixas de prenomes e
sobrenomes comuns, e e-mails usam o domínio reservado `example.com` (RFC 2606). Não há CPF,
CNPJ, telefone nem endereço completo. As marcas de produtos são inventadas.
