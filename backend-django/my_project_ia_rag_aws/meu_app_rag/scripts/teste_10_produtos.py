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

# 🧪 10 PRODUTOS DE TESTE
produtos_teste = [
    {
        "nome": "Camiseta Básica Branca",
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
        "dimensoes": "30x25x2cm",
        "imagem_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=500"
    },
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
        "dimensoes": "35x25x5cm",
        "imagem_url": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=500"
    },
    {
        "nome": "Tênis Corrida Pro Run",
        "categoria": "Calçados",
        "subcategoria": "Tênis",
        "preco": 199.90,
        "preco_promocional": 149.90,
        "marca": "SportPro",
        "cor": "Branco/Azul",
        "tamanho": "42",
        "material": "Tecido respirável mesh",
        "estoque": 30,
        "descricao": "Tênis leve para corrida com amortecimento de alta performance",
        "especificacoes": "Solado EVA, palmilha anatômica, respirável",
        "avaliacao": 4.8,
        "num_avaliacoes": 250,
        "peso": 0.35,
        "dimensoes": "30x12x10cm",
        "imagem_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=500"
    },
    {
        "nome": "Smartwatch Fitness Pro",
        "categoria": "Eletrônicos",
        "subcategoria": "Wearables",
        "preco": 599.90,
        "preco_promocional": 449.90,
        "marca": "TechFit",
        "cor": "Preto",
        "material": "Silicone e alumínio",
        "estoque": 42,
        "descricao": "Smartwatch com monitor cardíaco, GPS e bateria de 7 dias",
        "especificacoes": "Tela AMOLED 1.4', Bluetooth 5.0, IP68, Android/iOS",
        "avaliacao": 4.8,
        "num_avaliacoes": 892,
        "peso": 0.045,
        "dimensoes": "4.5x4.5x1.2cm",
        "imagem_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500"
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
        "descricao": "Mochila com compartimento para notebook 15.6' e USB charging port",
        "especificacoes": "Zíperes ocultos, bolso RFID, alças ergonômicas, 25L",
        "avaliacao": 4.5,
        "num_avaliacoes": 324,
        "peso": 0.8,
        "dimensoes": "45x30x15cm",
        "imagem_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500"
    },
    {
        "nome": "Perfume Masculino Intense",
        "categoria": "Beleza",
        "subcategoria": "Perfumes",
        "preco": 289.90,
        "marca": "FragrancePro",
        "cor": "N/A",
        "material": "Eau de Parfum",
        "estoque": 45,
        "descricao": "Perfume masculino sofisticado com notas amadeiradas e cítricas",
        "especificacoes": "100ml, concentração 15%, notas: bergamota, cedro e âmbar",
        "avaliacao": 4.9,
        "num_avaliacoes": 567,
        "peso": 0.3,
        "dimensoes": "12x6x6cm",
        "imagem_url": "https://images.unsplash.com/photo-1541643600914-78b084683601?w=500"
    },
    {
        "nome": "Fone Bluetooth Premium",
        "categoria": "Eletrônicos",
        "subcategoria": "Áudio",
        "preco": 399.90,
        "marca": "SoundMax",
        "cor": "Branco",
        "material": "Plástico ABS",
        "estoque": 53,
        "descricao": "Fone over-ear com cancelamento ativo de ruído e 30h de bateria",
        "especificacoes": "ANC, aptX HD, Bluetooth 5.2, dobrável, case incluso",
        "avaliacao": 4.8,
        "num_avaliacoes": 712,
        "peso": 0.25,
        "dimensoes": "20x18x8cm",
        "imagem_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500"
    },
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
        "dimensoes": "35x30x5cm",
        "imagem_url": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=500"
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
        "descricao": "Cadeira gamer com ajuste de altura, braços 4D e reclinável até 180°",
        "especificacoes": "Base metálica, rodas 360°, suporta até 150kg",
        "avaliacao": 4.7,
        "num_avaliacoes": 1034,
        "peso": 22.5,
        "dimensoes": "70x70x130cm",
        "imagem_url": "https://images.unsplash.com/photo-1598550476439-6847785fcea6?w=500"
    },
    {
        "nome": "Vestido Midi Floral",
        "categoria": "Roupas",
        "subcategoria": "Vestidos",
        "preco": 149.90,
        "preco_promocional": 119.90,
        "marca": "FlowerStyle",
        "cor": "Floral",
        "tamanho": "M",
        "material": "Viscose",
        "estoque": 34,
        "descricao": "Vestido midi com estampa floral romântica para ocasiões especiais",
        "especificacoes": "Alças finas, cintura marcada, forro interno",
        "avaliacao": 4.8,
        "num_avaliacoes": 678,
        "peso": 0.35,
        "dimensoes": "40x30x3cm",
        "imagem_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=500"
    },
]

print("🧪 TESTE: ADICIONANDO 10 PRODUTOS...\n")
print("=" * 60)

produtos_adicionados = 0
produtos_existentes = 0
produtos_com_imagem = 0

for dados in produtos_teste:
    existe = Produto.objects.filter(nome=dados['nome']).exists()
    
    if existe:
        print(f"⚠️  Já existe: {dados['nome']}")
        produtos_existentes += 1
    else:
        produto = Produto.objects.create(**dados)
        print(f"✅ Adicionado: {produto.nome}")
        print(f"   💰 Preço: R$ {produto.preco}")
        print(f"   📦 Estoque: {produto.estoque} unidades")
        
        if produto.tem_imagem():
            print(f"   📸 Imagem: {produto.get_imagem_url()[:50]}...")
            produtos_com_imagem += 1
        
        print()
        produtos_adicionados += 1

print("=" * 60)
print(f"\n📊 RESUMO DO TESTE:")
print("=" * 60)
print(f"   ✅ Produtos adicionados: {produtos_adicionados}")
print(f"   ⚠️  Já existiam: {produtos_existentes}")
print(f"   📸 Com imagem: {produtos_com_imagem}")
print(f"   📦 Total no catálogo: {Produto.objects.count()}")

print(f"\n🎯 ESTATÍSTICAS POR CATEGORIA:")
print("=" * 60)

from django.db.models import Count
categorias = Produto.objects.values('categoria').annotate(total=Count('id')).order_by('-total')
for cat in categorias:
    print(f"   📦 {cat['categoria']}: {cat['total']} produtos")

# Estatísticas por faixa de preço
print(f"\n💰 ESTATÍSTICAS POR PREÇO:")
print("=" * 60)
economicos = Produto.objects.filter(preco__lt=100).count()
intermediarios = Produto.objects.filter(preco__gte=100, preco__lt=300).count()
premium = Produto.objects.filter(preco__gte=300).count()

print(f"   💵 Econômicos (< R$ 100): {economicos}")
print(f"   💎 Intermediários (R$ 100-300): {intermediarios}")
print(f"   👑 Premium (> R$ 300): {premium}")

# Produtos com imagem
print(f"\n📸 PRODUTOS COM IMAGEM:")
print("=" * 60)
produtos_com_img = Produto.objects.exclude(imagem='', imagem_url__isnull=True)
for p in produtos_com_img[:5]:  # Mostrar apenas 5
    print(f"   • {p.nome}")
    print(f"     URL: {p.get_imagem_url()}")

print("\n" + "=" * 60)
print(f"⚡ PRÓXIMOS PASSOS:")
print("=" * 60)
print(f"   1. cd {project_root}")
print(f"   2. python manage.py popular_embeddings --force")
print(f"   3. Testar consulta RAG: http://localhost:8000/api/rag/query/")
print("=" * 60)