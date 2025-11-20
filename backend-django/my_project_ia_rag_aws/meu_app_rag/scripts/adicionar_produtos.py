import os
import sys
import django

# ⭐ AJUSTA O CAMINHO PARA A RAIZ DO PROJETO
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project_ia_rag_aws.settings')
django.setup()

from meu_app_rag.models import Produto

# 🆕 PRODUTOS DIVERSOS
produtos_diversos = [
    {
        "nome": "Bota Couro Masculina Premium",
        "categoria": "Calçados",
        "subcategoria": "Botas",
        "preco": 349.90,
        "preco_promocional": 279.90,
        "marca": "LeatherPro",
        "cor": "Marrom",
        "tamanho": "42",
        "material": "Couro legítimo",
        "estoque": 18,
        "descricao": "Bota masculina de couro legítimo, resistente e elegante para uso casual ou social",
        "especificacoes": "Solado antiderrapante, forro interno macio, costuras reforçadas",
        "avaliacao": 4.7,
        "num_avaliacoes": 156,
        "peso": 1.2,
        "dimensoes": "30x15x12cm"
    },
    {
        "nome": "Jaqueta Jeans Feminina",
        "categoria": "Roupas",
        "subcategoria": "Jaquetas",
        "preco": 159.90,
        "marca": "DenimStyle",
        "cor": "Azul",
        "tamanho": "M",
        "material": "100% algodão denim",
        "estoque": 25,
        "descricao": "Jaqueta jeans clássica, versátil e confortável para todas as estações",
        "especificacoes": "Botões de metal, dois bolsos frontais, lavagem estonada",
        "avaliacao": 4.6,
        "num_avaliacoes": 203,
        "peso": 0.6,
        "dimensoes": "45x40x5cm"
    },
    {
        "nome": "Relógio Smartwatch Fitness",
        "categoria": "Eletrônicos",
        "subcategoria": "Wearables",
        "preco": 599.90,
        "preco_promocional": 449.90,
        "marca": "TechFit",
        "cor": "Preto",
        "material": "Silicone e alumínio",
        "estoque": 42,
        "descricao": "Smartwatch com monitor cardíaco, GPS, à prova d'água e bateria de 7 dias",
        "especificacoes": "Tela AMOLED 1.4', Bluetooth 5.0, compatível Android/iOS, IP68",
        "avaliacao": 4.8,
        "num_avaliacoes": 892,
        "peso": 0.045,
        "dimensoes": "4.5x4.5x1.2cm"
    },
    {
        "nome": "Mochila Executiva Antifurto",
        "categoria": "Acessórios",
        "subcategoria": "Mochilas",
        "preco": 189.90,
        "marca": "SafeBag",
        "cor": "Cinza",
        "material": "Poliéster impermeável",
        "estoque": 67,
        "descricao": "Mochila com compartimento para notebook 15.6', USB charging port e proteção antifurto",
        "especificacoes": "Zíperes ocultos, bolso RFID, alças ergonômicas, capacidade 25L",
        "avaliacao": 4.5,
        "num_avaliacoes": 324,
        "peso": 0.8,
        "dimensoes": "45x30x15cm"
    },
    {
        "nome": "Perfume Importado Masculino",
        "categoria": "Beleza",
        "subcategoria": "Perfumes",
        "preco": 289.90,
        "marca": "FragrancePro",
        "cor": "N/A",
        "material": "Eau de Parfum",
        "estoque": 8,
        "descricao": "Perfume masculino sofisticado com notas amadeiradas e cítricas, longa duração",
        "especificacoes": "100ml, concentração 15%, notas de topo: bergamota e limão",
        "avaliacao": 4.9,
        "num_avaliacoes": 567,
        "peso": 0.3,
        "dimensoes": "12x6x6cm"
    },
    {
        "nome": "Cadeira Gamer Ergonômica",
        "categoria": "Móveis",
        "subcategoria": "Cadeiras",
        "preco": 899.90,
        "preco_promocional": 699.90,
        "marca": "GameSeats",
        "cor": "Preto/Vermelho",
        "material": "Couro sintético e espuma de alta densidade",
        "estoque": 15,
        "descricao": "Cadeira gamer com ajuste de altura, braços 4D, reclinável até 180°, suporta até 150kg",
        "especificacoes": "Base metálica, rodas 360°, almofadas lombar e cervical inclusas",
        "avaliacao": 4.7,
        "num_avaliacoes": 1034,
        "peso": 22.5,
        "dimensoes": "70x70x130cm"
    },
    {
        "nome": "Fone de Ouvido Bluetooth Premium",
        "categoria": "Eletrônicos",
        "subcategoria": "Áudio",
        "preco": 399.90,
        "marca": "SoundMax",
        "cor": "Branco",
        "material": "Plástico ABS",
        "estoque": 53,
        "descricao": "Fone over-ear com cancelamento ativo de ruído, 30h de bateria e qualidade Hi-Fi",
        "especificacoes": "ANC, aptX HD, Bluetooth 5.2, dobrável, case rígido incluso",
        "avaliacao": 4.8,
        "num_avaliacoes": 712,
        "peso": 0.25,
        "dimensoes": "20x18x8cm"
    },
    {
        "nome": "Bolsa Feminina Transversal",
        "categoria": "Acessórios",
        "subcategoria": "Bolsas",
        "preco": 129.90,
        "marca": "ChicBag",
        "cor": "Caramelo",
        "material": "Couro sintético premium",
        "estoque": 38,
        "descricao": "Bolsa transversal compacta e elegante, ideal para o dia a dia",
        "especificacoes": "Alça ajustável, 3 compartimentos internos, fecho magnético",
        "avaliacao": 4.4,
        "num_avaliacoes": 198,
        "peso": 0.4,
        "dimensoes": "25x20x8cm"
    },
]

# 👕 30 ROUPAS DIVERSIFICADAS
roupas = [
    # CAMISETAS
    {
        "nome": "Camiseta Manga Curta Lisa Branca",
        "categoria": "Roupas",
        "subcategoria": "Camisetas",
        "preco": 39.90,
        "marca": "BasicWear",
        "cor": "Branco",
        "tamanho": "M",
        "material": "100% algodão",
        "estoque": 150,
        "descricao": "Camiseta básica branca de algodão, perfeita para o dia a dia",
        "especificacoes": "Gola redonda, modelagem regular, malha de alta qualidade",
        "avaliacao": 4.3,
        "num_avaliacoes": 567,
        "peso": 0.2,
        "dimensoes": "30x25x2cm"
    },
    {
        "nome": "Camiseta Estampada Tropical",
        "categoria": "Roupas",
        "subcategoria": "Camisetas",
        "preco": 49.90,
        "marca": "TrendyStyle",
        "cor": "Multicolorido",
        "tamanho": "G",
        "material": "Algodão e poliéster",
        "estoque": 89,
        "descricao": "Camiseta com estampa tropical vibrante, ideal para o verão",
        "especificacoes": "Estampa digital, cores vivas, secagem rápida",
        "avaliacao": 4.5,
        "num_avaliacoes": 234,
        "peso": 0.22,
        "dimensoes": "32x27x2cm"
    },
    {
        "nome": "Camiseta Polo Masculina Premium",
        "categoria": "Roupas",
        "subcategoria": "Camisetas",
        "preco": 89.90,
        "preco_promocional": 69.90,
        "marca": "PoloClub",
        "cor": "Azul Marinho",
        "tamanho": "M",
        "material": "Piquet 100% algodão",
        "estoque": 45,
        "descricao": "Camisa polo elegante com bordado discreto, perfeita para ocasiões casuais",
        "especificacoes": "Botões frontais, gola estruturada, logo bordado",
        "avaliacao": 4.7,
        "num_avaliacoes": 412,
        "peso": 0.28,
        "dimensoes": "30x25x3cm"
    },
    {
        "nome": "Camiseta Regata Fitness Dry Fit",
        "categoria": "Roupas",
        "subcategoria": "Fitness",
        "preco": 44.90,
        "marca": "ActiveFit",
        "cor": "Preto",
        "tamanho": "M",
        "material": "Poliéster dry fit",
        "estoque": 120,
        "descricao": "Regata esportiva com tecnologia dry fit para treinos intensos",
        "especificacoes": "Secagem rápida, respirável, costura flatlock",
        "avaliacao": 4.6,
        "num_avaliacoes": 678,
        "peso": 0.15,
        "dimensoes": "28x23x1cm"
    },
    {
        "nome": "Camiseta Oversized Streetwear",
        "categoria": "Roupas",
        "subcategoria": "Camisetas",
        "preco": 79.90,
        "marca": "UrbanStyle",
        "cor": "Cinza",
        "tamanho": "G",
        "material": "Algodão premium",
        "estoque": 67,
        "descricao": "Camiseta oversized moderna com caimento largo, estilo urbano",
        "especificacoes": "Modelagem oversized, barra reta, estampa frontal",
        "avaliacao": 4.4,
        "num_avaliacoes": 189,
        "peso": 0.3,
        "dimensoes": "35x30x2cm"
    },
    
    # CALÇAS
    {
        "nome": "Calça Jeans Skinny Masculina",
        "categoria": "Roupas",
        "subcategoria": "Calças",
        "preco": 149.90,
        "marca": "DenimPro",
        "cor": "Azul Escuro",
        "tamanho": "42",
        "material": "98% algodão, 2% elastano",
        "estoque": 55,
        "descricao": "Calça jeans skinny masculina com elastano para maior conforto",
        "especificacoes": "5 bolsos, stretch, lavagem escura",
        "avaliacao": 4.5,
        "num_avaliacoes": 523,
        "peso": 0.6,
        "dimensoes": "35x25x5cm"
    },
    {
        "nome": "Calça Social Masculina Alfaiataria",
        "categoria": "Roupas",
        "subcategoria": "Calças",
        "preco": 189.90,
        "marca": "Elegance",
        "cor": "Preto",
        "tamanho": "44",
        "material": "Poliéster e viscose",
        "estoque": 38,
        "descricao": "Calça social de alfaiataria para ocasiões formais",
        "especificacoes": "Vinco marcado, bolsos traseiros, cós tradicional",
        "avaliacao": 4.6,
        "num_avaliacoes": 345,
        "peso": 0.5,
        "dimensoes": "35x25x4cm"
    },
    {
        "nome": "Calça Legging Fitness Feminina",
        "categoria": "Roupas",
        "subcategoria": "Fitness",
        "preco": 79.90,
        "marca": "GymGirl",
        "cor": "Preto",
        "tamanho": "M",
        "material": "Poliamida e elastano",
        "estoque": 145,
        "descricao": "Legging de cintura alta para treinos, máxima compressão e conforto",
        "especificacoes": "Cintura alta, tecido opaco, bolso para celular",
        "avaliacao": 4.8,
        "num_avaliacoes": 892,
        "peso": 0.25,
        "dimensoes": "30x20x3cm"
    },
    {
        "nome": "Calça Cargo Masculina Militar",
        "categoria": "Roupas",
        "subcategoria": "Calças",
        "preco": 129.90,
        "marca": "Military",
        "cor": "Verde Militar",
        "tamanho": "40",
        "material": "Sarja de algodão",
        "estoque": 72,
        "descricao": "Calça cargo estilo militar com múltiplos bolsos",
        "especificacoes": "6 bolsos laterais, ajuste no tornozelo, resistente",
        "avaliacao": 4.4,
        "num_avaliacoes": 267,
        "peso": 0.7,
        "dimensoes": "35x25x6cm"
    },
    {
        "nome": "Calça Jeans Mom Feminina",
        "categoria": "Roupas",
        "subcategoria": "Calças",
        "preco": 139.90,
        "marca": "TrendyJeans",
        "cor": "Azul Claro",
        "tamanho": "38",
        "material": "100% algodão denim",
        "estoque": 63,
        "descricao": "Calça jeans mom fit de cintura alta, estilo retrô moderno",
        "especificacoes": "Cintura alta, modelagem reta, lavagem clara",
        "avaliacao": 4.7,
        "num_avaliacoes": 456,
        "peso": 0.55,
        "dimensoes": "35x25x5cm"
    },
    
    # SHORTS
    {
        "nome": "Bermuda Jeans Masculina Destroyed",
        "categoria": "Roupas",
        "subcategoria": "Shorts",
        "preco": 89.90,
        "marca": "DenimStyle",
        "cor": "Azul",
        "tamanho": "40",
        "material": "Algodão denim",
        "estoque": 85,
        "descricao": "Bermuda jeans com detalhes destroyed, estilo casual",
        "especificacoes": "5 bolsos, rasgos discretos, barra desfiada",
        "avaliacao": 4.3,
        "num_avaliacoes": 198,
        "peso": 0.4,
        "dimensoes": "30x25x4cm"
    },
    {
        "nome": "Short Fitness Masculino Respirável",
        "categoria": "Roupas",
        "subcategoria": "Fitness",
        "preco": 54.90,
        "marca": "SportPro",
        "cor": "Preto",
        "tamanho": "M",
        "material": "Poliéster dry fit",
        "estoque": 132,
        "descricao": "Short esportivo leve e respirável para corrida e treinos",
        "especificacoes": "Secagem rápida, bolso com zíper, elástico no cós",
        "avaliacao": 4.6,
        "num_avaliacoes": 543,
        "peso": 0.18,
        "dimensoes": "25x20x2cm"
    },
    {
        "nome": "Short Saia Feminino Jeans",
        "categoria": "Roupas",
        "subcategoria": "Shorts",
        "preco": 69.90,
        "marca": "FashionGirl",
        "cor": "Azul",
        "tamanho": "M",
        "material": "Algodão denim",
        "estoque": 47,
        "descricao": "Short saia jeans moderno e versátil",
        "especificacoes": "Cintura alta, botões frontais, bolsos funcionais",
        "avaliacao": 4.4,
        "num_avaliacoes": 312,
        "peso": 0.3,
        "dimensoes": "25x20x3cm"
    },
    
    # VESTIDOS E SAIAS
    {
        "nome": "Vestido Midi Floral Feminino",
        "categoria": "Roupas",
        "subcategoria": "Vestidos",
        "preco": 149.90,
        "preco_promocional": 119.90,
        "marca": "FlowerStyle",
        "cor": "Floral",
        "tamanho": "M",
        "material": "Viscose",
        "estoque": 34,
        "descricao": "Vestido midi com estampa floral romântica, ideal para ocasiões especiais",
        "especificacoes": "Alças finas, cintura marcada, forro interno",
        "avaliacao": 4.8,
        "num_avaliacoes": 678,
        "peso": 0.35,
        "dimensoes": "40x30x3cm"
    },
    {
        "nome": "Vestido Longo Festa Elegante",
        "categoria": "Roupas",
        "subcategoria": "Vestidos",
        "preco": 299.90,
        "marca": "EleganceDress",
        "cor": "Vinho",
        "tamanho": "M",
        "material": "Cetim e renda",
        "estoque": 18,
        "descricao": "Vestido longo sofisticado para festas e eventos formais",
        "especificacoes": "Decote canoa, detalhes em renda, fenda lateral",
        "avaliacao": 4.9,
        "num_avaliacoes": 234,
        "peso": 0.5,
        "dimensoes": "45x35x4cm"
    },
    {
        "nome": "Saia Plissada Midi",
        "categoria": "Roupas",
        "subcategoria": "Saias",
        "preco": 89.90,
        "marca": "ChicStyle",
        "cor": "Nude",
        "tamanho": "M",
        "material": "Crepe plissado",
        "estoque": 56,
        "descricao": "Saia plissada elegante e versátil para diversas ocasiões",
        "especificacoes": "Cintura alta, elástico confortável, comprimento midi",
        "avaliacao": 4.5,
        "num_avaliacoes": 421,
        "peso": 0.25,
        "dimensoes": "30x25x3cm"
    },
    {
        "nome": "Saia Jeans Curta Destroyed",
        "categoria": "Roupas",
        "subcategoria": "Saias",
        "preco": 79.90,
        "marca": "DenimGirl",
        "cor": "Azul",
        "tamanho": "M",
        "material": "Algodão denim",
        "estoque": 68,
        "descricao": "Saia jeans curta com detalhes destroyed, estilo jovem",
        "especificacoes": "Botões frontais, rasgos discretos, bolsos",
        "avaliacao": 4.3,
        "num_avaliacoes": 289,
        "peso": 0.28,
        "dimensoes": "25x22x3cm"
    },
    
    # BLUSAS E TOPS
    {
        "nome": "Blusa Cropped Canelada",
        "categoria": "Roupas",
        "subcategoria": "Blusas",
        "preco": 44.90,
        "marca": "TrendTop",
        "cor": "Preto",
        "tamanho": "M",
        "material": "Malha canelada",
        "estoque": 98,
        "descricao": "Blusa cropped canelada básica e moderna",
        "especificacoes": "Modelagem justa, manga longa, comprimento cropped",
        "avaliacao": 4.4,
        "num_avaliacoes": 512,
        "peso": 0.15,
        "dimensoes": "25x20x2cm"
    },
    {
        "nome": "Blusa Social Feminina Manga Longa",
        "categoria": "Roupas",
        "subcategoria": "Blusas",
        "preco": 99.90,
        "marca": "OfficeWear",
        "cor": "Branco",
        "tamanho": "M",
        "material": "Viscose",
        "estoque": 43,
        "descricao": "Blusa social elegante para ambiente corporativo",
        "especificacoes": "Botões frontais, punhos com botão, modelagem clássica",
        "avaliacao": 4.6,
        "num_avaliacoes": 367,
        "peso": 0.22,
        "dimensoes": "30x25x2cm"
    },
    {
        "nome": "Top Fitness Strappy",
        "categoria": "Roupas",
        "subcategoria": "Fitness",
        "preco": 59.90,
        "marca": "ActiveFit",
        "cor": "Rosa",
        "tamanho": "M",
        "material": "Poliamida e elastano",
        "estoque": 87,
        "descricao": "Top fitness com tiras cruzadas nas costas, máximo suporte",
        "especificacoes": "Bojo removível, compressão média, respirável",
        "avaliacao": 4.7,
        "num_avaliacoes": 634,
        "peso": 0.12,
        "dimensoes": "22x18x2cm"
    },
    {
        "nome": "Blusa Gola Alta Tricot",
        "categoria": "Roupas",
        "subcategoria": "Blusas",
        "preco": 89.90,
        "marca": "WinterWear",
        "cor": "Caramelo",
        "tamanho": "M",
        "material": "Tricot acrílico",
        "estoque": 52,
        "descricao": "Blusa de tricot com gola alta, perfeita para o inverno",
        "especificacoes": "Gola alta, manga longa, trama fechada",
        "avaliacao": 4.5,
        "num_avaliacoes": 298,
        "peso": 0.35,
        "dimensoes": "30x25x4cm"
    },
    
    # MOLETONS E CASACOS
    {
        "nome": "Moletom Canguru Unissex",
        "categoria": "Roupas",
        "subcategoria": "Moletons",
        "preco": 119.90,
        "marca": "ComfortWear",
        "cor": "Cinza Mescla",
        "tamanho": "M",
        "material": "Algodão e poliéster",
        "estoque": 76,
        "descricao": "Moletom canguru clássico com capuz e bolso frontal",
        "especificacoes": "Capuz com cordão, bolso canguru, felpa interna",
        "avaliacao": 4.7,
        "num_avaliacoes": 845,
        "peso": 0.6,
        "dimensoes": "35x30x5cm"
    },
    {
        "nome": "Moletom Zíper Masculino Sport",
        "categoria": "Roupas",
        "subcategoria": "Moletons",
        "preco": 139.90,
        "marca": "SportStyle",
        "cor": "Preto",
        "tamanho": "G",
        "material": "Algodão e poliéster",
        "estoque": 64,
        "descricao": "Moletom esportivo com zíper frontal e capuz",
        "especificacoes": "Zíper resistente, 2 bolsos laterais, ribana nos punhos",
        "avaliacao": 4.6,
        "num_avaliacoes": 432,
        "peso": 0.7,
        "dimensoes": "35x30x5cm"
    },
    {
        "nome": "Casaco Bomber Unissex",
        "categoria": "Roupas",
        "subcategoria": "Casacos",
        "preco": 179.90,
        "preco_promocional": 149.90,
        "marca": "UrbanJacket",
        "cor": "Verde Militar",
        "tamanho": "M",
        "material": "Nylon",
        "estoque": 41,
        "descricao": "Jaqueta bomber estilo aviador, design moderno",
        "especificacoes": "Zíper frontal, bolsos laterais, ribana nos punhos",
        "avaliacao": 4.8,
        "num_avaliacoes": 523,
        "peso": 0.5,
        "dimensoes": "40x35x5cm"
    },
    {
        "nome": "Jaqueta Corta Vento Impermeável",
        "categoria": "Roupas",
        "subcategoria": "Casacos",
        "preco": 159.90,
        "marca": "OutdoorPro",
        "cor": "Azul",
        "tamanho": "M",
        "material": "Poliéster impermeável",
        "estoque": 55,
        "descricao": "Jaqueta corta vento leve e impermeável para atividades ao ar livre",
        "especificacoes": "Capuz removível, bolsos com zíper, costuras seladas",
        "avaliacao": 4.5,
        "num_avaliacoes": 389,
        "peso": 0.4,
        "dimensoes": "38x33x4cm"
    },
    {
        "nome": "Colete Puffer Feminino",
        "categoria": "Roupas",
        "subcategoria": "Casacos",
        "preco": 129.90,
        "marca": "WarmStyle",
        "cor": "Preto",
        "tamanho": "M",
        "material": "Nylon com enchimento sintético",
        "estoque": 48,
        "descricao": "Colete puffer acolchoado e moderno",
        "especificacoes": "Sem mangas, zíper frontal, bolsos laterais",
        "avaliacao": 4.6,
        "num_avaliacoes": 276,
        "peso": 0.35,
        "dimensoes": "35x30x6cm"
    },
    
    # CONJUNTOS
    {
        "nome": "Conjunto Moletom Feminino",
        "categoria": "Roupas",
        "subcategoria": "Conjuntos",
        "preco": 179.90,
        "marca": "ComfortSet",
        "cor": "Rosa",
        "tamanho": "M",
        "material": "Algodão e poliéster",
        "estoque": 39,
        "descricao": "Conjunto de moletom com blusa cropped e calça jogger",
        "especificacoes": "Blusa cropped, calça com elástico e cordão, felpa interna",
        "avaliacao": 4.7,
        "num_avaliacoes": 456,
        "peso": 0.8,
        "dimensoes": "35x30x6cm"
    },
    {
        "nome": "Conjunto Fitness Top e Legging",
        "categoria": "Roupas",
        "subcategoria": "Fitness",
        "preco": 119.90,
        "marca": "GymSet",
        "cor": "Preto e Pink",
        "tamanho": "M",
        "material": "Poliamida e elastano",
        "estoque": 71,
        "descricao": "Conjunto fitness com top e legging combinando",
        "especificacoes": "Top com bojo, legging de cintura alta, tecido respirável",
        "avaliacao": 4.8,
        "num_avaliacoes": 789,
        "peso": 0.4,
        "dimensoes": "30x25x4cm"
    },
    {
        "nome": "Pijama Masculino Conforto",
        "categoria": "Roupas",
        "subcategoria": "Pijamas",
        "preco": 89.90,
        "marca": "SleepWell",
        "cor": "Azul Marinho",
        "tamanho": "M",
        "material": "100% algodão",
        "estoque": 93,
        "descricao": "Pijama masculino confortável para noites tranquilas",
        "especificacoes": "Camiseta manga curta, calça com elástico, macio",
        "avaliacao": 4.5,
        "num_avaliacoes": 345,
        "peso": 0.45,
        "dimensoes": "30x25x5cm"
    },
    {
        "nome": "Pijama Feminino Cetim",
        "categoria": "Roupas",
        "subcategoria": "Pijamas",
        "preco": 109.90,
        "marca": "LuxSleep",
        "cor": "Champagne",
        "tamanho": "M",
        "material": "Cetim sintético",
        "estoque": 57,
        "descricao": "Pijama feminino em cetim com detalhes de renda",
        "especificacoes": "Blusa com alças, short curto, acabamento em renda",
        "avaliacao": 4.6,
        "num_avaliacoes": 412,
        "peso": 0.3,
        "dimensoes": "28x23x4cm"
    },
    
    # OUTROS
    {
        "nome": "Camisa Social Masculina Slim",
        "categoria": "Roupas",
        "subcategoria": "Camisas",
        "preco": 129.90,
        "marca": "Elegance",
        "cor": "Branco",
        "tamanho": "M",
        "material": "Algodão egípcio",
        "estoque": 62,
        "descricao": "Camisa social slim fit de alta qualidade para ocasiões formais",
        "especificacoes": "Corte slim, botões de madrepérola, fácil de passar",
        "avaliacao": 4.7,
        "num_avaliacoes": 534,
        "peso": 0.3,
        "dimensoes": "30x25x3cm"
    },
    {
        "nome": "Suéter Gola V Masculino",
        "categoria": "Roupas",
        "subcategoria": "Blusas",
        "preco": 99.90,
        "marca": "ClassicMen",
        "cor": "Cinza",
        "tamanho": "M",
        "material": "Lã e acrílico",
        "estoque": 44,
        "descricao": "Suéter clássico de gola V para o inverno",
        "especificacoes": "Gola V, manga longa, trama fechada",
        "avaliacao": 4.4,
        "num_avaliacoes": 267,
        "peso": 0.4,
        "dimensoes": "32x28x4cm"
    },
]

# Combinar todas as listas
todos_produtos = produtos_diversos + roupas

print("🚀 ADICIONANDO NOVOS PRODUTOS...\n")

produtos_adicionados = 0
produtos_existentes = 0

for dados in todos_produtos:
    existe = Produto.objects.filter(nome=dados['nome']).exists()
    
    if existe:
        print(f"⚠️  Já existe: {dados['nome']}")
        produtos_existentes += 1
    else:
        produto = Produto.objects.create(**dados)
        print(f"✅ Adicionado: {produto.nome} (ID: {produto.id})")
        produtos_adicionados += 1

print(f"\n📊 RESUMO:")
print(f"   ✅ Produtos adicionados: {produtos_adicionados}")
print(f"   ⚠️  Já existiam: {produtos_existentes}")
print(f"   📦 Total no catálogo: {Produto.objects.count()}")
print(f"\n🎯 ESTATÍSTICAS POR CATEGORIA:")

from django.db.models import Count
categorias = Produto.objects.values('categoria').annotate(total=Count('id')).order_by('-total')
for cat in categorias:
    print(f"   📦 {cat['categoria']}: {cat['total']} produtos")

print(f"\n⚡ PRÓXIMO PASSO:")
print(f"   cd {project_root}")
print(f"   python manage.py popular_embeddings --force")

## rode python .\adicionar_produtos.py
## # 2. Regenere os embeddings (ISSO INJETA O CONHECIMENTO!)
## python manage.py popular_embeddings --force