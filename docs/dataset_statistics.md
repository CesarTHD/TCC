# Estatísticas do dataset

> Documento **gerado automaticamente** por `python seed/stats.py` a partir de consultas
> executadas no banco populado (seed = 42, data de referência = 2026-09-30).
> Não editar à mão.
>
> **Uso metodológico:** este documento descreve o dataset para o texto do TCC. Ele
> **não** deve ser fornecido como contexto às arquiteturas NL2SQL avaliadas, pois
> contém resultados agregados que poderiam funcionar como gabarito.

Regras usadas nos números abaixo (ver `metadata/business_rules.json`): faturamento,
ticket médio e quantidade vendida consideram apenas pedidos `CONCLUIDO`.

## 1. Registros por tabela

| tabela | registros |
|---|---|
| categorias | 10 |
| produtos | 222 |
| vendedores | 25 |
| clientes | 2.000 |
| pedidos | 12.073 |
| itens_pedido | 32.669 |

## 2. Período coberto

| coluna | mínimo | máximo |
|---|---|---|
| pedidos.data_pedido | 2023-01-01 | 2026-09-30 |
| clientes.data_cadastro | 2021-01-01 | 2026-09-29 |
| produtos.data_cadastro | 2021-03-01 | 2026-08-20 |
| vendedores.data_admissao | 2016-08-07 | 2025-06-28 |

Cadastros de clientes, produtos e vendedores podem ser anteriores a 2023 (base pré-existente);
pedidos existem somente de 2023-01-01 a 2026-09-30. O ano de 2026 está incompleto (jan–set).

## 3. Indicadores gerais

| indicador | valor |
|---|---|
| Faturamento total (pedidos CONCLUIDO) | R$ 11.737.649,15 |
| Ticket médio (pedidos CONCLUIDO) | R$ 1.042,98 |
| Ticket mediano (pedidos CONCLUIDO) | R$ 617,62 |
| Clientes sem nenhum pedido | 326 |
| Clientes com pelo menos um pedido CONCLUIDO (compraram) | 1.623 |
| Clientes com pedidos, mas nenhum CONCLUIDO | 51 |
| Maior número de pedidos de um único cliente | 63 |
| Itens (de pedidos CONCLUIDO) com desconto | 29,78% |
| Total de descontos concedidos (pedidos CONCLUIDO) | R$ 360.521,53 |
| Produtos nunca vendidos | 1 |
| UFs sem clientes | 3 |

## 4. Pedidos por status

| status | pedidos | % | soma de valor_total (R$) |
|---|---|---|---|
| CONCLUIDO | 11.254 | 93,22 | 11.737.649,15 |
| CANCELADO | 663 | 5,49 | 701.942,74 |
| PENDENTE | 156 | 1,29 | 172.108,99 |

## 5. Pedidos por ano

| ano | pedidos | concluídos | cancelados | pendentes | faturamento (R$) |
|---|---|---|---|---|---|
| 2023 | 1.786 | 1.670 | 116 | 0 | 1.706.543,43 |
| 2024 | 2.690 | 2.543 | 147 | 0 | 2.603.383,76 |
| 2025 | 3.865 | 3.639 | 226 | 0 | 3.783.518,26 |
| 2026 | 3.732 | 3.402 | 174 | 156 | 3.644.203,70 |

## 6. Pedidos por mês e ano (sazonalidade)

| mês | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| 1 | 96 | 152 | 207 | 329 |
| 2 | 96 | 144 | 203 | 306 |
| 3 | 113 | 178 | 270 | 409 |
| 4 | 118 | 192 | 268 | 375 |
| 5 | 157 | 254 | 290 | 453 |
| 6 | 115 | 187 | 296 | 478 |
| 7 | 139 | 210 | 343 | 452 |
| 8 | 164 | 223 | 356 | 472 |
| 9 | 121 | 230 | 305 | 458 |
| 10 | 150 | 227 | 347 | 0 |
| 11 | 243 | 299 | 424 | 0 |
| 12 | 274 | 394 | 556 | 0 |

## 7. Pedidos por canal de venda

| canal | pedidos | % dos pedidos | % cancelados no canal |
|---|---|---|---|
| SITE | 4.837 | 40,06 | 6,99 |
| LOJA | 3.632 | 30,08 | 2,84 |
| APP | 2.821 | 23,37 | 5,42 |
| TELEFONE | 783 | 6,49 | 8,81 |

Participação (%) dos canais por ano:

| ano | SITE | LOJA | APP | TELEFONE |
|---|---|---|---|---|
| 2023 | 43,30 | 34,80 | 12,00 | 9,80 |
| 2024 | 40,20 | 32,50 | 19,10 | 8,10 |
| 2025 | 40,30 | 28,80 | 25,40 | 5,60 |
| 2026 | 38,20 | 27,40 | 29,80 | 4,70 |

## 8. Clientes por UF

| UF | clientes | % |
|---|---|---|
| SP | 586 | 29,30 |
| RJ | 256 | 12,80 |
| MG | 179 | 8,95 |
| RS | 126 | 6,30 |
| PR | 115 | 5,75 |
| BA | 93 | 4,65 |
| DF | 76 | 3,80 |
| SC | 72 | 3,60 |
| PE | 71 | 3,55 |
| CE | 69 | 3,45 |
| GO | 52 | 2,60 |
| AM | 45 | 2,25 |
| RN | 37 | 1,85 |
| MS | 27 | 1,35 |
| MT | 27 | 1,35 |
| PA | 26 | 1,30 |
| PB | 25 | 1,25 |
| ES | 23 | 1,15 |
| AL | 20 | 1,00 |
| MA | 20 | 1,00 |
| PI | 19 | 0,95 |
| SE | 15 | 0,75 |
| TO | 13 | 0,65 |
| RO | 8 | 0,40 |

## 9. Clientes por quantidade de pedidos (qualquer status)

| faixa | clientes |
|---|---|
| 0 pedidos | 326 |
| 1 pedido | 476 |
| 2 a 5 | 515 |
| 6 a 20 | 574 |
| 21 ou mais | 109 |

Atributos cadastrais:

| atributo | valor | clientes |
|---|---|---|
| segmento | PADRAO | 1.675 |
| segmento | PREMIUM | 325 |
| status | ATIVO | 1.800 |
| status | INATIVO | 200 |

## 10. Pedidos por quantidade de itens

| itens no pedido | pedidos |
|---|---|
| 1 | 3.632 |
| 2 | 3.038 |
| 3 | 2.203 |
| 4 | 1.422 |
| 5 | 922 |
| 6 | 369 |
| 7 | 252 |
| 8 | 99 |
| 9 | 76 |
| 10 | 60 |

## 11. Categorias (pedidos CONCLUIDO)

| categoria | produtos vendidos | unidades | faturamento (R$) | % do faturamento |
|---|---|---|---|---|
| Eletrônicos | 24 | 5.463 | 2.203.855,88 | 18,78 |
| Informática | 24 | 2.339 | 2.065.300,86 | 17,60 |
| Eletrodomésticos | 23 | 2.139 | 1.774.349,60 | 15,12 |
| Moda | 21 | 5.970 | 1.116.948,22 | 9,52 |
| Casa e Decoração | 24 | 5.093 | 944.511,09 | 8,05 |
| Esporte e Lazer | 21 | 5.079 | 878.901,46 | 7,49 |
| Beleza e Cuidados Pessoais | 21 | 6.964 | 864.188,29 | 7,36 |
| Livros e Papelaria | 21 | 10.089 | 677.326,90 | 5,77 |
| Móveis | 21 | 757 | 607.373,68 | 5,17 |
| Brinquedos | 21 | 4.291 | 604.893,17 | 5,15 |

## 12. Top 10 produtos por quantidade vendida

| produto | categoria | unidades | faturamento (R$) |
|---|---|---|---|
| Garrafa Térmica Trilhar | Esporte e Lazer | 2.315 | 189.139,50 |
| Calça Jeans Urbanna | Moda | 2.023 | 297.995,42 |
| Livro de Ficção Letra Viva | Livros e Papelaria | 1.559 | 86.219,70 |
| Planner Semanal Grafitto | Livros e Papelaria | 1.489 | 76.767,22 |
| Câmera de Segurança Wi-Fi Voltrix | Eletrônicos | 1.426 | 409.856,25 |
| Calculadora Científica Letra Viva | Livros e Papelaria | 1.381 | 155.258,40 |
| Protetor Solar FPS 50 Pelebela | Beleza e Cuidados Pessoais | 1.304 | 47.049,36 |
| Planner Semanal Papiro Azul | Livros e Papelaria | 1.179 | 37.157,55 |
| Barbeador Elétrico Pelebela | Beleza e Cuidados Pessoais | 975 | 209.383,22 |
| Camiseta Básica Urbanna | Moda | 939 | 73.775,65 |

## 13. Top 10 produtos por faturamento

| produto | categoria | unidades | faturamento (R$) |
|---|---|---|---|
| Notebook 15 polegadas Bytera | Informática | 264 | 1.005.501,15 |
| Geladeira Frost Free Casaflux | Eletrodomésticos | 263 | 581.239,07 |
| Câmera de Segurança Wi-Fi Voltrix | Eletrônicos | 1.426 | 409.856,25 |
| Geladeira Frost Free Termika | Eletrodomésticos | 136 | 381.745,12 |
| Tablet 10 polegadas Voltrix | Eletrônicos | 224 | 322.920,54 |
| Calça Jeans Urbanna | Moda | 2.023 | 297.995,42 |
| Caixa de Som Portátil Nexalume | Eletrônicos | 522 | 248.841,01 |
| Notebook 15 polegadas Pixelar | Informática | 36 | 220.198,87 |
| Barbeador Elétrico Pelebela | Beleza e Cuidados Pessoais | 975 | 209.383,22 |
| Garrafa Térmica Trilhar | Esporte e Lazer | 2.315 | 189.139,50 |

## 14. Vendedores (pedidos CONCLUIDO), ordenados por faturamento

| vendedor | região | status | vendas | faturamento (R$) |
|---|---|---|---|---|
| Ricardo Cavalcanti Siqueira | SUDESTE | ATIVO | 1.099 | 1.145.892,18 |
| André Oliveira Almeida | SUDESTE | ATIVO | 1.003 | 1.032.005,09 |
| Vanessa Fonseca Silva | NORTE | ATIVO | 771 | 798.019,83 |
| Heitor Andrade Moura | SUL | ATIVO | 797 | 786.304,94 |
| Juliana Rezende Carvalho | SUDESTE | ATIVO | 634 | 663.206,14 |
| Isabela Cavalcanti Oliveira | NORDESTE | ATIVO | 645 | 645.364,91 |
| Bruno Araújo Marques | CENTRO-OESTE | ATIVO | 664 | 624.340,23 |
| Natália Araújo Rodrigues | SUDESTE | ATIVO | 608 | 612.114,85 |
| Rodrigo Soares Siqueira | SUDESTE | ATIVO | 483 | 547.867,72 |
| Leonardo Santos Campos | SUL | ATIVO | 462 | 514.063,30 |
| Yasmin Mendes Pereira | SUDESTE | INATIVO | 495 | 508.134,42 |
| André Gonçalves Farias | CENTRO-OESTE | ATIVO | 466 | 505.506,98 |
| Daniel Ferreira Almeida | NORDESTE | ATIVO | 433 | 460.309,44 |
| Eduardo Pereira Peixoto | SUL | ATIVO | 413 | 423.862,36 |
| Clara Rodrigues Pinto | SUDESTE | ATIVO | 380 | 380.186,26 |
| Yasmin Batista Nunes | NORDESTE | ATIVO | 322 | 358.428,16 |
| Vanessa Pinto Oliveira | NORDESTE | ATIVO | 269 | 265.517,76 |
| Marcelo Fernandes Fonseca | SUDESTE | INATIVO | 256 | 260.409,45 |
| Valéria Barbosa Tavares | SUDESTE | ATIVO | 184 | 216.686,23 |
| Vinícius Ribeiro Correia | NORDESTE | INATIVO | 228 | 212.629,54 |
| Patrícia Dias Rocha | NORDESTE | ATIVO | 167 | 179.012,34 |
| Clara Tavares Gomes | NORTE | ATIVO | 135 | 173.060,66 |
| Rafaela Fernandes Araújo | SUL | INATIVO | 128 | 165.284,10 |
| Bianca Lopes Freitas | CENTRO-OESTE | ATIVO | 117 | 149.313,90 |
| Lucas Tavares Rodrigues | NORTE | ATIVO | 95 | 110.128,36 |

## 15. Produtos ativos e inativos

| situação | produtos |
|---|---|
| ativos | 204 |
| inativos | 18 |

## 16. Checksums de reprodutibilidade

Digest SHA-256 do gerador (Python): `494cbdf84aa2d9aced64c09d531e31be497d189f202a34a2469381fb94583a33`

MD5 do conteúdo de cada tabela (`database/checksums.sql`):

| tabela | linhas | md5 |
|---|---|---|
| categorias | 10 | `8ab122e74db78a3747be7ac78784a606` |
| produtos | 222 | `40ff5a04dddb2ca6677cb1099a58b344` |
| vendedores | 25 | `e894960185ecfbb559cf0358f1734caa` |
| clientes | 2.000 | `0a18d57520a883ddd46108fab704be37` |
| pedidos | 12.073 | `9b923531e00a698c3536b491bfaa5747` |
| itens_pedido | 32.669 | `67330a37d96229eaf8bb19ad1737989b` |
