# Geração dos dados sintéticos

Código: `seed/generator.py` (algoritmo) e `seed/reference_data.py` (listas e parâmetros).
Números reais resultantes: `docs/dataset_statistics.md`.

## 1. Determinismo

- `generate(seed=42)` é uma função pura: não acessa banco, relógio nem rede.
- Toda a aleatoriedade vem de **uma** instância `random.Random(42)`, consumida sempre na mesma
  ordem: categorias → produtos → vendedores → clientes → pedidos/itens.
- A data de referência é a constante `2026-09-30`. Nenhum valor depende da data de execução.
- IDs são inteiros atribuídos pelo gerador, sem sequences. Os pedidos são numerados em ordem
  cronológica (data, cliente, sequência).
- Valores monetários usam `decimal.Decimal`, com arredondamento `ROUND_HALF_UP` a 2 casas.
- **Faker não é usado.** A saída do Faker muda entre versões da biblioteca, o que quebraria a
  reprodutibilidade de longo prazo. Nomes, cidades e produtos vêm de listas fixas versionadas
  no repositório, sorteadas com o mesmo gerador aleatório.
- Verificação: `Dataset.digest()` (SHA-256 de todas as linhas), `database/checksums.sql`
  (MD5 por tabela no banco) e o teste que compara o banco linha a linha com o gerador.

## 2. Etapas e distribuições

### Categorias e produtos
- 10 categorias. Cada uma tem 7–8 itens-base com faixa de preço plausível e 3 marcas
  fictícias (linhas econômica ×0,80, intermediária ×1,00 e premium ×1,30): 222 produtos.
- Preço atual = preço-base sorteado na faixa × multiplicador da linha, terminando em ",90".
- `data_cadastro`: 65% entre 2021-03 e 2022-12 (catálogo pré-existente); 35% entre 2023-01
  e 2026-08 (lançamentos ao longo do período).
- Popularidade (peso de sorteio nas vendas), em quatro fatores:
  `peso_categoria × peso_linha × 1/rank^0,8 × 1/√(preço/100)`.
  - peso_categoria: de 0,5 (Móveis) a 1,5 (Moda);
  - peso_linha: econômica 1,2, intermediária 1,0, premium 0,65;
  - rank: posição aleatória do produto dentro da categoria (lei de potência, que gera produtos campeões e produtos de cauda);
  - fator de preço: itens caros são comprados com menos frequência.
- 18 produtos (~8%) são **descontinuados** (`ativo = false`). Eles vendem apenas até uma data
  interna de descontinuação (entre 2024 e 2026-06), que não é armazenada.

### Vendedores
- 25 vendedores: Sudeste 9, Nordeste 6, Sul 4, Centro-Oeste 3, Norte 3.
- Os 2 primeiros de cada região são veteranos (admitidos antes de 2023) que nunca são
  desligados. Isso garante vendedor disponível em todas as regiões durante todo o período.
- Os demais são admitidos antes de 2023 (55%) ou entre 2023-02 e 2025-12.
- Exatamente 4 vendedores admitidos antes de 2023 são desligados (`INATIVO`), com
  `data_desligamento` entre 2024-03 e 2026-06.
- Desempenho heterogêneo: peso log-normal (σ = 0,6) usado no sorteio do vendedor de cada pedido.

### Clientes
- 2.000 clientes. 22% cadastrados em 2021–2022; os demais entre 2023-01-01 e 2026-09-30,
  com mistura de distribuição uniforme e triangular crescente (a base cresce com o tempo).
- Idade no cadastro: triangular(18, 75, moda 32).
- Cidade/UF: 35 cidades de 24 UFs com pesos não uniformes (a cidade de São Paulo tem ~19% do peso
  total e o estado de SP ~30%). AC, AP e RR não têm clientes.
- `segmento`: 15% PREMIUM. `status`: 10% INATIVO, sorteado independentemente das compras.
- Perfil de compra (oculto, não armazenado), com pesos diferentes para PADRAO e PREMIUM:

| perfil | PADRAO | PREMIUM | pedidos |
|---|---|---|---|
| nunca | 9% | 3% | 0 |
| único | 16% | 7% | exatamente 1 |
| ocasional | 46% | 35% | Poisson(1,8 × anos ativos) |
| frequente | 25% | 40% | Poisson(5 × anos ativos) |
| intenso | 4% | 15% | Poisson(14 × anos ativos) |

"Anos ativos" vai de max(cadastro, 2023-01-01) até 2026-09-30. Por isso clientes recentes
têm menos pedidos, e alguns clientes recentes de perfil ocasional também ficam sem pedidos.

### Pedidos
- **Data**: uniforme na janela ativa do cliente, aceita por amostragem por rejeição com peso
  mensal (sazonalidade moderada): jan/fev 0,85; mai 1,10; nov 1,35; dez 1,50; demais 0,95–1,00.
- **Vendedor**: entre os vendedores em atividade na data (admissão ≤ data ≤ desligamento),
  com 75% de chance de ser da região do cliente; sorteio ponderado pelo desempenho.
- **Canal**: participação varia por ano. APP cresce de 13% (2023) para 30% (2026) e TELEFONE
  cai de 10% para 5%.
- **Status**:
  - pedidos com até 14 dias antes da referência: 45% PENDENTE;
  - de 15 a 45 dias: 12% PENDENTE;
  - mais antigos: nunca PENDENTE;
  - não pendentes: CANCELADO com probabilidade por canal (LOJA 3%, APP 6%, SITE 7%,
    TELEFONE 10%), e os demais CONCLUIDO.
- **Itens por pedido**: 1 (30%), 2 (25%), 3 (18%), 4 (12%), 5 (8%), 6–10 (7%).

### Itens
- Produtos sorteados sem reposição, por popularidade, entre os disponíveis na data
  (`data_cadastro ≤ data ≤ fim de vendas`).
- `preco_unitario` = preço atual deflacionado por 4,5% a.a. até a data do pedido.
  O preço histórico é, portanto, menor que o atual e cresce com o tempo.
- `quantidade` depende do preço unitário: até R$ 100, de 1 a 6 unidades; até R$ 500, de 1 a 3;
  acima disso, 1 ou 2 (90%/10%).
- `desconto`: com probabilidade de 25% (PADRAO) ou 45% (PREMIUM), aplica-se 5%, 10%, 15% ou
  20% sobre o valor bruto, arredondado ao centavo.
- `valor_total_item = quantidade × preco_unitario − desconto`; `pedidos.valor_total` é a soma
  dos itens.

## 3. Características garantidas (verificadas em testes)

Clientes sem pedido, com 1 pedido, com vários e com dezenas de pedidos; concentração geográfica;
vendedores com volumes diferentes (≥ 4× entre maior e menor); produtos e categorias com
participações distintas; pedidos em 2023–2026; sazonalidade; os 3 status e os 4 canais;
pedidos de 1 a 10 itens; produtos ativos e inativos; vendedores ativos e desligados.

## 4. Decisões e limitações

- **Inativação de produtos**: a data de descontinuação não é armazenada (não existe coluna para
  isso). Ela só limita as vendas. O banco informa apenas `ativo = false`.
- **Status de cliente** independente das compras, por especificação. Pode haver cliente
  INATIVO com pedido recente.
- **Vendedor em canais digitais**: todo pedido tem vendedor (responsável pela conta), inclusive
  SITE e APP, para manter `vendedor_id` NOT NULL e o modelo simples.
- **Cadastros anteriores a 2023**: clientes, produtos e vendedores podem ter sido cadastrados
  antes de 2023, mas pedidos só existem a partir de 2023-01-01.
- **Crescimento**: o volume anual cresce porque a base de clientes cresce, e 2026 está
  incompleto (até setembro). Comparações entre anos devem considerar isso.
- **Determinismo entre versões do Python**: o algoritmo de `random.Random` (Mersenne Twister) e
  os métodos usados são estáveis no Python 3. A geração foi verificada com Python 3.14. O
  digest em `docs/dataset_statistics.md` permite detectar qualquer divergência.
