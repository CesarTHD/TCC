"""Dados de referência fixos usados pelo gerador.

Tudo aqui é fictício. As listas são estáticas (em vez de Faker) para que a
geração não dependa da versão de nenhuma biblioteca externa: a mesma seed
produz sempre o mesmo dataset.
"""

# ---------------------------------------------------------------------------
# Nomes (combinações aleatórias de prenome + 2 sobrenomes => pessoas fictícias)
# ---------------------------------------------------------------------------
PRENOMES = [
    "Ana", "Bruno", "Camila", "Daniel", "Eduarda", "Felipe", "Gabriela", "Gustavo",
    "Helena", "Igor", "Isabela", "João", "Juliana", "Kauã", "Larissa", "Leonardo",
    "Letícia", "Lucas", "Luana", "Marcelo", "Mariana", "Mateus", "Natália", "Otávio",
    "Paula", "Pedro", "Rafaela", "Rafael", "Renata", "Rodrigo", "Sabrina", "Samuel",
    "Tatiana", "Thiago", "Vanessa", "Vinícius", "Yasmin", "André", "Beatriz", "Carlos",
    "Débora", "Eduardo", "Fernanda", "Fábio", "Giovana", "Henrique", "Jéssica", "José",
    "Karina", "Luiz", "Maria", "Miguel", "Patrícia", "Ricardo", "Sofia", "Tiago",
    "Valéria", "Wellington", "Alice", "Arthur", "Bianca", "Caio", "Clara", "Diego",
    "Elisa", "Fabiana", "Heitor", "Lívia", "Manuela", "Nicolas",
]

SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
    "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes",
    "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade",
    "Moreira", "Nunes", "Marques", "Machado", "Mendes", "Freitas", "Cardoso", "Ramos",
    "Gonçalves", "Santana", "Teixeira", "Araújo", "Pinto", "Correia", "Cavalcanti", "Moura",
    "Campos", "Monteiro", "Batista", "Duarte", "Barros", "Farias", "Castro", "Medeiros",
    "Rezende", "Peixoto", "Siqueira", "Queiroz", "Fonseca", "Brandão", "Macedo", "Tavares",
]

# Domínio reservado pela IANA (RFC 2606) — nunca corresponde a e-mails reais.
EMAIL_DOMINIO_CLIENTES = "example.com"
EMAIL_DOMINIO_VENDEDORES = "vendas.example.com"

# ---------------------------------------------------------------------------
# Geografia
# ---------------------------------------------------------------------------
REGIAO_POR_UF = {
    "AC": "NORTE", "AM": "NORTE", "AP": "NORTE", "PA": "NORTE", "RO": "NORTE", "RR": "NORTE", "TO": "NORTE",
    "AL": "NORDESTE", "BA": "NORDESTE", "CE": "NORDESTE", "MA": "NORDESTE", "PB": "NORDESTE",
    "PE": "NORDESTE", "PI": "NORDESTE", "RN": "NORDESTE", "SE": "NORDESTE",
    "DF": "CENTRO-OESTE", "GO": "CENTRO-OESTE", "MS": "CENTRO-OESTE", "MT": "CENTRO-OESTE",
    "ES": "SUDESTE", "MG": "SUDESTE", "RJ": "SUDESTE", "SP": "SUDESTE",
    "PR": "SUL", "RS": "SUL", "SC": "SUL",
}

# (cidade, uf, peso). Pesos não uniformes => concentração em capitais do Sudeste.
# AC, AP e RR propositalmente não possuem clientes.
CIDADES = [
    ("São Paulo", "SP", 220), ("Campinas", "SP", 45), ("Ribeirão Preto", "SP", 22),
    ("Santos", "SP", 20), ("Sorocaba", "SP", 18), ("São José dos Campos", "SP", 18),
    ("Rio de Janeiro", "RJ", 120), ("Niterói", "RJ", 22),
    ("Belo Horizonte", "MG", 70), ("Uberlândia", "MG", 20), ("Juiz de Fora", "MG", 15),
    ("Vitória", "ES", 15),
    ("Curitiba", "PR", 60), ("Londrina", "PR", 18),
    ("Florianópolis", "SC", 25), ("Joinville", "SC", 18),
    ("Porto Alegre", "RS", 50), ("Caxias do Sul", "RS", 15),
    ("Salvador", "BA", 50), ("Recife", "PE", 42), ("Fortaleza", "CE", 42),
    ("Natal", "RN", 15), ("João Pessoa", "PB", 14), ("Maceió", "AL", 12),
    ("Aracaju", "SE", 10), ("São Luís", "MA", 12), ("Teresina", "PI", 10),
    ("Brasília", "DF", 45), ("Goiânia", "GO", 30), ("Cuiabá", "MT", 12), ("Campo Grande", "MS", 12),
    ("Manaus", "AM", 22), ("Belém", "PA", 20), ("Palmas", "TO", 6), ("Porto Velho", "RO", 6),
]

# ---------------------------------------------------------------------------
# Vendedores: (regiao, quantidade)
# ---------------------------------------------------------------------------
VENDEDORES_POR_REGIAO = [
    ("SUDESTE", 9), ("NORDESTE", 6), ("SUL", 4), ("CENTRO-OESTE", 3), ("NORTE", 3),
]

# ---------------------------------------------------------------------------
# Catálogo
# Cada categoria: nome, descrição, peso de popularidade nas vendas,
# 3 marcas fictícias (linha econômica, intermediária, premium) e
# itens-base (nome, preço mínimo, preço máximo) em R$.
# Produto final = "<item-base> <marca>" => 3 produtos por item-base.
# ---------------------------------------------------------------------------
MULTIPLICADOR_LINHA = (0.80, 1.00, 1.30)   # econômica, intermediária, premium
POPULARIDADE_LINHA = (1.20, 1.00, 0.65)

CATEGORIAS = [
    {
        "nome": "Eletrônicos",
        "descricao": "Smartphones, áudio, vídeo, wearables e acessórios eletrônicos.",
        "popularidade": 1.40,
        "marcas": ("Voltrix", "Nexalume", "Orbitel"),
        "itens": [
            ("Smartphone 128GB", 1200, 2500), ("Fone de Ouvido Bluetooth", 120, 450),
            ("Smart TV 50 polegadas", 2200, 3500), ("Caixa de Som Portátil", 150, 600),
            ("Smartwatch", 400, 1500), ("Tablet 10 polegadas", 900, 2200),
            ("Carregador Turbo USB-C", 60, 150), ("Câmera de Segurança Wi-Fi", 180, 400),
        ],
    },
    {
        "nome": "Informática",
        "descricao": "Computadores, periféricos, armazenamento e redes.",
        "popularidade": 1.00,
        "marcas": ("Bytera", "Kodexa", "Pixelar"),
        "itens": [
            ("Notebook 15 polegadas", 2800, 5500), ("Monitor 24 polegadas", 700, 1300),
            ("Teclado Mecânico", 200, 550), ("Mouse Sem Fio", 60, 200),
            ("SSD 1TB", 350, 700), ("Impressora Multifuncional", 700, 1500),
            ("Roteador Wi-Fi 6", 300, 800), ("Webcam Full HD", 180, 400),
        ],
    },
    {
        "nome": "Eletrodomésticos",
        "descricao": "Eletrodomésticos de cozinha, lavanderia e climatização.",
        "popularidade": 0.90,
        "marcas": ("Casaflux", "Termika", "Brisalar"),
        "itens": [
            ("Geladeira Frost Free", 2800, 5000), ("Micro-ondas 30L", 550, 1000),
            ("Air Fryer 4L", 350, 700), ("Liquidificador", 150, 350),
            ("Aspirador de Pó", 300, 800), ("Cafeteira Elétrica", 120, 450),
            ("Máquina de Lavar 12kg", 2000, 3500), ("Ventilador de Coluna", 180, 350),
        ],
    },
    {
        "nome": "Móveis",
        "descricao": "Móveis para sala, quarto, cozinha e escritório.",
        "popularidade": 0.50,
        "marcas": ("Madeirol", "Confortex", "Lignare"),
        "itens": [
            ("Sofá 3 Lugares", 1800, 3500), ("Cadeira de Escritório", 500, 1400),
            ("Mesa de Jantar 4 Lugares", 900, 2200), ("Guarda-Roupa 6 Portas", 1100, 2500),
            ("Estante para Livros", 300, 700), ("Rack para TV", 400, 900),
            ("Cama Box Casal", 1200, 2600),
        ],
    },
    {
        "nome": "Casa e Decoração",
        "descricao": "Cama, mesa, banho, utilidades domésticas e decoração.",
        "popularidade": 1.20,
        "marcas": ("Lumiar", "Tecelar", "Aconchega"),
        "itens": [
            ("Jogo de Cama Casal", 150, 380), ("Toalha de Banho", 40, 110),
            ("Luminária de Mesa", 90, 250), ("Tapete para Sala", 180, 600),
            ("Conjunto de Panelas", 300, 800), ("Jogo de Copos", 50, 140),
            ("Cortina Blackout", 120, 300), ("Quadro Decorativo", 80, 260),
        ],
    },
    {
        "nome": "Esporte e Lazer",
        "descricao": "Artigos esportivos, fitness, ciclismo e camping.",
        "popularidade": 0.80,
        "marcas": ("Atletix", "Trilhar", "Movimentta"),
        "itens": [
            ("Bicicleta Aro 29", 1300, 2800), ("Tênis de Corrida", 280, 700),
            ("Halteres 10kg", 120, 280), ("Tapete de Yoga", 70, 180),
            ("Barraca de Camping", 300, 900), ("Bola de Futebol", 80, 220),
            ("Garrafa Térmica", 60, 160),
        ],
    },
    {
        "nome": "Moda",
        "descricao": "Roupas, calçados casuais e acessórios.",
        "popularidade": 1.50,
        "marcas": ("Urbanna", "Tramaviva", "Estilare"),
        "itens": [
            ("Camiseta Básica", 40, 110), ("Calça Jeans", 130, 280),
            ("Jaqueta Corta-Vento", 180, 450), ("Vestido Midi", 150, 350),
            ("Bolsa de Couro", 250, 700), ("Óculos de Sol", 150, 500),
            ("Mochila Urbana", 130, 350),
        ],
    },
    {
        "nome": "Beleza e Cuidados Pessoais",
        "descricao": "Perfumaria, cosméticos, higiene e aparelhos de cuidado pessoal.",
        "popularidade": 1.30,
        "marcas": ("Pelebela", "Aromaris", "Cuidarte"),
        "itens": [
            ("Perfume 100ml", 180, 550), ("Secador de Cabelo", 150, 400),
            ("Kit Skincare", 90, 260), ("Barbeador Elétrico", 150, 450),
            ("Shampoo 400ml", 25, 70), ("Protetor Solar FPS 50", 40, 110),
            ("Prancha Alisadora", 120, 380),
        ],
    },
    {
        "nome": "Livros e Papelaria",
        "descricao": "Livros, cadernos, agendas e material de escritório.",
        "popularidade": 1.10,
        "marcas": ("Papiro Azul", "Letra Viva", "Grafitto"),
        "itens": [
            ("Livro de Ficção", 35, 90), ("Livro Técnico", 80, 220),
            ("Caderno Universitário", 25, 60), ("Kit Canetas", 20, 70),
            ("Agenda Anual", 40, 110), ("Planner Semanal", 40, 100),
            ("Calculadora Científica", 60, 160),
        ],
    },
    {
        "nome": "Brinquedos",
        "descricao": "Brinquedos, jogos e itens infantis.",
        "popularidade": 0.70,
        "marcas": ("Brincalê", "Ludiquê", "Cirandinha"),
        "itens": [
            ("Blocos de Montar 500 peças", 150, 400), ("Boneca Articulada", 90, 250),
            ("Carrinho de Controle Remoto", 150, 450), ("Quebra-Cabeça 1000 peças", 60, 140),
            ("Jogo de Tabuleiro", 100, 280), ("Pelúcia", 50, 150),
            ("Patinete Infantil", 200, 450),
        ],
    },
]

# ---------------------------------------------------------------------------
# Comportamento temporal e comercial
# ---------------------------------------------------------------------------
# Sazonalidade moderada (peso relativo por mês) — pico em nov/dez, vale em jan/fev.
PESO_MES = {1: 0.85, 2: 0.85, 3: 0.95, 4: 0.95, 5: 1.10, 6: 1.00,
            7: 1.00, 8: 1.00, 9: 0.95, 10: 1.00, 11: 1.35, 12: 1.50}

# Participação dos canais por ano (SITE, LOJA, APP, TELEFONE): APP cresce, TELEFONE cai.
CANAIS = ("SITE", "LOJA", "APP", "TELEFONE")
PESO_CANAL_POR_ANO = {
    2023: (42, 35, 13, 10),
    2024: (41, 32, 19, 8),
    2025: (40, 29, 25, 6),
    2026: (38, 27, 30, 5),
}

# Probabilidade de cancelamento por canal (aplicada a pedidos que não estão pendentes).
PROB_CANCELAMENTO = {"SITE": 0.07, "LOJA": 0.03, "APP": 0.06, "TELEFONE": 0.10}

# Pedidos PENDENTES só existem perto da data de referência:
# (idade máxima do pedido em dias, probabilidade de estar pendente)
FAIXAS_PENDENTE = ((14, 0.45), (45, 0.12))

# Número de itens distintos por pedido: (quantidade de itens, peso)
DISTRIBUICAO_ITENS = ((1, 30), (2, 25), (3, 18), (4, 12), (5, 8), (6, 3), (7, 2), (8, 1), (9, 0.6), (10, 0.4))

# Perfis de compra dos clientes: (perfil, peso PADRAO, peso PREMIUM, pedidos/ano)
# "nunca" => 0 pedidos; "unico" => exatamente 1 pedido; demais => Poisson(taxa * anos).
PERFIS_COMPRA = (
    ("nunca",     0.09, 0.03, 0.0),
    ("unico",     0.16, 0.07, None),
    ("ocasional", 0.46, 0.35, 1.8),
    ("frequente", 0.25, 0.40, 5.0),
    ("intenso",   0.04, 0.15, 14.0),
)

# Inflação anual usada para derivar o preço histórico a partir do preço atual.
INFLACAO_ANUAL = 0.045

# Descontos: probabilidade de o item ter desconto por segmento e percentuais possíveis.
PROB_DESCONTO = {"PADRAO": 0.25, "PREMIUM": 0.45}
PERCENTUAIS_DESCONTO = ((5, 40), (10, 30), (15, 20), (20, 10))
