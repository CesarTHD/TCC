-- =============================================================================
-- TCC NL2SQL — Schema do dataset experimental
-- PostgreSQL 16
--
-- Cria o schema "dataset" e suas 6 tabelas. Idempotente apenas em banco vazio:
-- para recriar do zero use database/reset.sql.
--
-- Convenções:
--   * IDs inteiros atribuídos explicitamente pelo gerador (seed/), sem sequences,
--     para que a geração seja 100% determinística.
--   * Valores monetários em NUMERIC(12,2) (nunca FLOAT).
--   * Datas em DATE (granularidade diária).
--   * Valores categóricos em VARCHAR + CHECK (mais simples de documentar e de
--     consultar via NL2SQL do que tipos ENUM).
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS dataset;

COMMENT ON SCHEMA dataset IS
    'Dataset experimental sintético (vendas) para avaliação de arquiteturas NL2SQL. Data de referência: 2026-09-30.';

-- -----------------------------------------------------------------------------
-- categorias
-- -----------------------------------------------------------------------------
CREATE TABLE dataset.categorias (
    id          INTEGER      PRIMARY KEY,
    nome        VARCHAR(60)  NOT NULL UNIQUE,
    descricao   VARCHAR(255) NOT NULL
);

COMMENT ON TABLE  dataset.categorias           IS 'Categorias (departamentos) de produtos.';
COMMENT ON COLUMN dataset.categorias.id        IS 'Identificador da categoria.';
COMMENT ON COLUMN dataset.categorias.nome      IS 'Nome da categoria.';
COMMENT ON COLUMN dataset.categorias.descricao IS 'Descrição textual da categoria.';

-- -----------------------------------------------------------------------------
-- produtos
-- -----------------------------------------------------------------------------
CREATE TABLE dataset.produtos (
    id             INTEGER       PRIMARY KEY,
    categoria_id   INTEGER       NOT NULL REFERENCES dataset.categorias (id),
    nome           VARCHAR(120)  NOT NULL UNIQUE,
    descricao      VARCHAR(255)  NOT NULL,
    preco          NUMERIC(12,2) NOT NULL CHECK (preco > 0),
    ativo          BOOLEAN       NOT NULL,
    data_cadastro  DATE          NOT NULL CHECK (data_cadastro <= DATE '2026-09-30')
);

COMMENT ON TABLE  dataset.produtos               IS 'Catálogo de produtos.';
COMMENT ON COLUMN dataset.produtos.id            IS 'Identificador do produto.';
COMMENT ON COLUMN dataset.produtos.categoria_id  IS 'Categoria do produto (FK categorias.id).';
COMMENT ON COLUMN dataset.produtos.nome          IS 'Nome comercial do produto.';
COMMENT ON COLUMN dataset.produtos.descricao     IS 'Descrição textual do produto.';
COMMENT ON COLUMN dataset.produtos.preco         IS 'Preço de tabela ATUAL (na data de referência 2026-09-30). Não é o preço praticado em vendas passadas; ver itens_pedido.preco_unitario.';
COMMENT ON COLUMN dataset.produtos.ativo         IS 'TRUE = produto ativo no catálogo; FALSE = descontinuado (pode ter vendas históricas).';
COMMENT ON COLUMN dataset.produtos.data_cadastro IS 'Data de inclusão do produto no catálogo. Nenhuma venda ocorre antes desta data.';

-- -----------------------------------------------------------------------------
-- clientes
-- -----------------------------------------------------------------------------
CREATE TABLE dataset.clientes (
    id               INTEGER      PRIMARY KEY,
    nome             VARCHAR(120) NOT NULL,
    email            VARCHAR(160) NOT NULL UNIQUE,
    data_nascimento  DATE         NOT NULL,
    data_cadastro    DATE         NOT NULL CHECK (data_cadastro <= DATE '2026-09-30'),
    cidade           VARCHAR(80)  NOT NULL,
    uf               CHAR(2)      NOT NULL CHECK (uf IN (
                         'AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT','PA',
                         'PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO')),
    segmento         VARCHAR(10)  NOT NULL CHECK (segmento IN ('PADRAO', 'PREMIUM')),
    status           VARCHAR(10)  NOT NULL CHECK (status IN ('ATIVO', 'INATIVO')),
    CHECK (data_nascimento < data_cadastro)
);

COMMENT ON TABLE  dataset.clientes                 IS 'Clientes (pessoas físicas fictícias) cadastrados.';
COMMENT ON COLUMN dataset.clientes.id              IS 'Identificador do cliente.';
COMMENT ON COLUMN dataset.clientes.nome            IS 'Nome completo (fictício).';
COMMENT ON COLUMN dataset.clientes.email           IS 'E-mail fictício (domínio reservado example.com).';
COMMENT ON COLUMN dataset.clientes.data_nascimento IS 'Data de nascimento.';
COMMENT ON COLUMN dataset.clientes.data_cadastro   IS 'Data de cadastro do cliente. Nenhum pedido do cliente é anterior a ela.';
COMMENT ON COLUMN dataset.clientes.cidade          IS 'Cidade de residência.';
COMMENT ON COLUMN dataset.clientes.uf              IS 'Sigla da unidade federativa (estado).';
COMMENT ON COLUMN dataset.clientes.segmento        IS 'Plano de relacionamento: PADRAO ou PREMIUM (programa de fidelidade).';
COMMENT ON COLUMN dataset.clientes.status          IS 'Situação cadastral atual: ATIVO ou INATIVO. Independente de o cliente ter comprado.';

-- -----------------------------------------------------------------------------
-- vendedores
-- -----------------------------------------------------------------------------
CREATE TABLE dataset.vendedores (
    id                 INTEGER      PRIMARY KEY,
    nome               VARCHAR(120) NOT NULL,
    email              VARCHAR(160) NOT NULL UNIQUE,
    data_admissao      DATE         NOT NULL CHECK (data_admissao <= DATE '2026-09-30'),
    data_desligamento  DATE         NULL     CHECK (data_desligamento <= DATE '2026-09-30'),
    regiao             VARCHAR(12)  NOT NULL CHECK (regiao IN ('NORTE', 'NORDESTE', 'CENTRO-OESTE', 'SUDESTE', 'SUL')),
    status             VARCHAR(10)  NOT NULL CHECK (status IN ('ATIVO', 'INATIVO')),
    CHECK (data_desligamento IS NULL OR data_desligamento > data_admissao),
    -- INATIVO <=> possui data de desligamento
    CHECK ((status = 'INATIVO') = (data_desligamento IS NOT NULL))
);

COMMENT ON TABLE  dataset.vendedores                   IS 'Vendedores responsáveis pelos pedidos.';
COMMENT ON COLUMN dataset.vendedores.id                IS 'Identificador do vendedor.';
COMMENT ON COLUMN dataset.vendedores.nome              IS 'Nome completo (fictício).';
COMMENT ON COLUMN dataset.vendedores.email             IS 'E-mail corporativo fictício (domínio reservado example.com).';
COMMENT ON COLUMN dataset.vendedores.data_admissao     IS 'Data de admissão. Nenhum pedido do vendedor é anterior a ela.';
COMMENT ON COLUMN dataset.vendedores.data_desligamento IS 'Data de desligamento (NULL se ainda ativo). Nenhum pedido do vendedor é posterior a ela.';
COMMENT ON COLUMN dataset.vendedores.regiao            IS 'Região do Brasil em que o vendedor atua.';
COMMENT ON COLUMN dataset.vendedores.status            IS 'ATIVO (sem desligamento) ou INATIVO (desligado).';

-- -----------------------------------------------------------------------------
-- pedidos
-- -----------------------------------------------------------------------------
CREATE TABLE dataset.pedidos (
    id           INTEGER       PRIMARY KEY,
    cliente_id   INTEGER       NOT NULL REFERENCES dataset.clientes (id),
    vendedor_id  INTEGER       NOT NULL REFERENCES dataset.vendedores (id),
    data_pedido  DATE          NOT NULL CHECK (data_pedido BETWEEN DATE '2023-01-01' AND DATE '2026-09-30'),
    status       VARCHAR(10)   NOT NULL CHECK (status IN ('CONCLUIDO', 'CANCELADO', 'PENDENTE')),
    canal_venda  VARCHAR(10)   NOT NULL CHECK (canal_venda IN ('SITE', 'LOJA', 'APP', 'TELEFONE')),
    valor_total  NUMERIC(12,2) NOT NULL CHECK (valor_total >= 0)
);

COMMENT ON TABLE  dataset.pedidos             IS 'Pedidos de venda (cabeçalho). Pedidos CANCELADOS e PENDENTES permanecem armazenados.';
COMMENT ON COLUMN dataset.pedidos.id          IS 'Identificador do pedido (crescente em ordem cronológica).';
COMMENT ON COLUMN dataset.pedidos.cliente_id  IS 'Cliente que fez o pedido (FK clientes.id).';
COMMENT ON COLUMN dataset.pedidos.vendedor_id IS 'Vendedor responsável pelo pedido (FK vendedores.id). Todo pedido tem vendedor, inclusive canais digitais.';
COMMENT ON COLUMN dataset.pedidos.data_pedido IS 'Data em que o pedido foi realizado.';
COMMENT ON COLUMN dataset.pedidos.status      IS 'CONCLUIDO (venda efetivada), CANCELADO ou PENDENTE (ainda não concluído).';
COMMENT ON COLUMN dataset.pedidos.canal_venda IS 'Canal de venda: SITE, LOJA, APP ou TELEFONE.';
COMMENT ON COLUMN dataset.pedidos.valor_total IS 'Soma de itens_pedido.valor_total_item do pedido. Para faturamento considerar apenas status = CONCLUIDO.';

-- -----------------------------------------------------------------------------
-- itens_pedido
-- -----------------------------------------------------------------------------
CREATE TABLE dataset.itens_pedido (
    id                INTEGER       PRIMARY KEY,
    pedido_id         INTEGER       NOT NULL REFERENCES dataset.pedidos (id),
    produto_id        INTEGER       NOT NULL REFERENCES dataset.produtos (id),
    quantidade        INTEGER       NOT NULL CHECK (quantidade > 0),
    preco_unitario    NUMERIC(12,2) NOT NULL CHECK (preco_unitario > 0),
    desconto          NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (desconto >= 0),
    valor_total_item  NUMERIC(12,2) NOT NULL CHECK (valor_total_item >= 0),
    UNIQUE (pedido_id, produto_id),
    CHECK (desconto <= quantidade * preco_unitario),
    CHECK (valor_total_item = quantidade * preco_unitario - desconto)
);

COMMENT ON TABLE  dataset.itens_pedido                  IS 'Itens (linhas) de cada pedido. Um produto aparece no máximo uma vez por pedido.';
COMMENT ON COLUMN dataset.itens_pedido.id               IS 'Identificador do item.';
COMMENT ON COLUMN dataset.itens_pedido.pedido_id        IS 'Pedido ao qual o item pertence (FK pedidos.id).';
COMMENT ON COLUMN dataset.itens_pedido.produto_id       IS 'Produto vendido (FK produtos.id).';
COMMENT ON COLUMN dataset.itens_pedido.quantidade       IS 'Quantidade de unidades (> 0).';
COMMENT ON COLUMN dataset.itens_pedido.preco_unitario   IS 'Preço unitário praticado na data do pedido (histórico; pode diferir de produtos.preco).';
COMMENT ON COLUMN dataset.itens_pedido.desconto         IS 'Desconto total do item em R$ (não é percentual).';
COMMENT ON COLUMN dataset.itens_pedido.valor_total_item IS 'quantidade * preco_unitario - desconto.';

-- -----------------------------------------------------------------------------
-- Índices (ver docs/database.md, seção "Índices")
-- PKs e UNIQUE já criam índices implicitamente; itens_pedido(pedido_id, produto_id)
-- já é coberto pela UNIQUE, portanto não há índice separado em pedido_id.
-- -----------------------------------------------------------------------------
CREATE INDEX idx_produtos_categoria_id    ON dataset.produtos (categoria_id);
CREATE INDEX idx_pedidos_cliente_id       ON dataset.pedidos (cliente_id);
CREATE INDEX idx_pedidos_vendedor_id      ON dataset.pedidos (vendedor_id);
CREATE INDEX idx_pedidos_data_pedido      ON dataset.pedidos (data_pedido);
CREATE INDEX idx_itens_pedido_produto_id  ON dataset.itens_pedido (produto_id);
