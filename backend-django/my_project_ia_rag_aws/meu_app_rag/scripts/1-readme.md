# 🧠 COMO É REALIZADO O "INPUTAR CONHECIMENTO" - EXPLICAÇÃO COMPLETA

---

## 📊 FLUXO COMPLETO EM 3 ETAPAS

```
┌──────────────────────────────────────────────────────────────┐
│ ETAPA 1: ADICIONAR PRODUTOS NO BANCO DE DADOS               │
│ Arquivo: adicionar_produtos.py                              │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ ETAPA 2: GERAR EMBEDDINGS                                   │
│ Comando: python manage.py popular_embeddings --force        │
└──────────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────────┐
│ ETAPA 3: BUSCA VETORIAL NO RAG                              │
│ Arquivo: retriever.py                                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎯 ETAPA 1: ADICIONAR NO BANCO (adicionar_produtos.py)

### O que acontece:

```python
# Script: adicionar_produtos.py

produto = Produto.objects.create(
    nome="Camiseta Básica Branca",
    categoria="Roupas",
    preco=39.90,
    descricao="Camiseta básica de algodão",
    # ... outros campos
)
```

### SQL executado (por trás do Django ORM):

```sql
INSERT INTO meu_app_rag_produto (
    nome, 
    categoria, 
    preco, 
    descricao,
    ...
) VALUES (
    'Camiseta Básica Branca',
    'Roupas',
    39.90,
    'Camiseta básica de algodão',
    ...
);
```

### Resultado:

```
PostgreSQL/SQLite
├── Tabela: meu_app_rag_produto
│   ├── ID: 1 | Nome: Camiseta Básica
│   ├── ID: 2 | Nome: Calça Jeans
│   ├── ID: 3 | Nome: Tênis Corrida
│   └── ...
```

**⚠️ IMPORTANTE:** Neste ponto, os dados estão APENAS no banco de dados relacional. O RAG ainda NÃO consegue buscar por eles!

---

## 🧠 ETAPA 2: GERAR EMBEDDINGS (popular_embeddings.py)

### Comando:
```bash
python manage.py popular_embeddings --force
```

### O que acontece INTERNAMENTE:

#### **Passo 2.1: LER DO BANCO**

```python
# popular_embeddings.py - exportar_catalogo()

produtos = Produto.objects.all()  # ← SQL: SELECT * FROM produtos

catalogo = {}
for p in produtos:
    catalogo[p.id] = {
        'id': p.id,
        'nome': p.nome,
        'descricao': p.descricao,
        'categoria': p.categoria,
        'preco': float(p.preco),
        # ... todos os campos
    }

# Salva em arquivo pickle
with open('db_data/catalogo.pkl', 'wb') as f:
    pickle.dump(catalogo, f)
```

**Resultado:** Arquivo `catalogo.pkl` com todos os produtos

```python
# Conteúdo do catalogo.pkl
{
    1: {
        'id': 1,
        'nome': 'Camiseta Básica Branca',
        'categoria': 'Roupas',
        'preco': 39.90,
        'descricao': 'Camiseta básica de algodão...',
        # ... todos os campos
    },
    2: {
        'id': 2,
        'nome': 'Calça Jeans Skinny',
        # ...
    },
    # ... 43 produtos
}
```

---

#### **Passo 2.2: GERAR EMBEDDINGS (AQUI É A MÁGICA!)**

```python
# popular_embeddings.py - gerar_embeddings()

emb = Embeddings()  # Conecta com AWS Bedrock

ids = []
vectors = []

for pid, produto in catalogo.items():
    # 1. Criar texto descritivo
    texto = f"{produto['nome']}. {produto['descricao']}. Categoria: {produto['categoria']}"
    
    # Exemplo:
    # "Camiseta Básica Branca. Camiseta básica de algodão. Categoria: Roupas"
    
    # 2. Normalizar (lowercase, sem acentos)
    texto_norm = unidecode(texto.lower())
    # "camiseta basica branca. camiseta basica de algodao. categoria: roupas"
    
    # 3. ENVIAR PARA AWS BEDROCK TITAN EMBEDDINGS
    vetor = emb.embed(texto_norm)
    
    # Retorna um vetor de 1024 números:
    # [0.234, -0.127, 0.891, 0.456, ..., -0.321]
    
    ids.append(pid)
    vectors.append(vetor)
```

### 🌐 O QUE ACONTECE NA AWS BEDROCK:

```
Texto: "camiseta basica branca..."
         ↓
┌─────────────────────────────────┐
│   AWS BEDROCK                    │
│   Amazon Titan Embeddings v2     │
│                                  │
│   Modelo de Machine Learning     │
│   treinado em bilhões de textos  │
│                                  │
│   Converte texto em vetor que    │
│   representa o SIGNIFICADO       │
└─────────────────────────────────┘
         ↓
Vetor: [0.234, -0.127, 0.891, ..., -0.321]
       ↑
       1024 dimensões (números float)
```

**Por que 1024 números?**
- Cada número representa uma "característica semântica"
- Exemplo hipotético:
  - Dimensão 1: "é roupa?" → 0.9 (sim!)
  - Dimensão 2: "é eletrônico?" → 0.1 (não!)
  - Dimensão 3: "é casual?" → 0.8 (sim!)
  - Dimensão 4: "é confortável?" → 0.7 (sim!)
  - ... 1020 dimensões a mais

---

#### **Passo 2.3: SALVAR VETORES**

```python
# Salvar em arquivo pickle
with open('db_data/vectors.pkl', 'wb') as f:
    pickle.dump({
        'ids': [1, 2, 3, 4, ...],
        'vectors': np.array([
            [0.234, -0.127, 0.891, ...],  # Vetor do produto 1
            [0.198, -0.115, 0.870, ...],  # Vetor do produto 2
            [0.050, 0.230, -0.450, ...],  # Vetor do produto 3
            # ... 43 vetores
        ])
    }, f)
```

**Resultado:** Arquivo `vectors.pkl`

```python
# Estrutura do vectors.pkl
{
    'ids': [1, 2, 3, 4, 5, ..., 43],
    'vectors': numpy.array([
        [0.234, -0.127, ...],  # 1024 números
        [0.198, -0.115, ...],  # 1024 números
        # ... 43 linhas (uma por produto)
    ])
}
```

---

## 🔍 ETAPA 3: BUSCA VETORIAL (retriever.py)

### Quando usuário faz uma consulta:

```python
# Usuario pergunta:
query = "Quero uma camiseta confortável"
```

### O que acontece:

#### **Passo 3.1: GERAR EMBEDDING DA PERGUNTA**

```python
# retriever.py - retrieve()

# 1. Normaliza
query_norm = "quero uma camiseta confortavel"

# 2. Gera embedding da pergunta (AWS Bedrock)
query_vector = embedding.embed(query_norm)
# Retorna: [0.240, -0.130, 0.895, ..., -0.318]
```

---

#### **Passo 3.2: COMPARAR COM TODOS OS PRODUTOS**

```python
# 3. Carrega vetores dos produtos (do arquivo pickle)
product_vectors = [
    [0.234, -0.127, 0.891, ...],  # Produto 1: Camiseta Básica
    [0.198, -0.115, 0.870, ...],  # Produto 2: Calça Jeans
    [0.050, 0.230, -0.450, ...],  # Produto 3: Tênis
    # ... 43 produtos
]

query_vector = [0.240, -0.130, 0.895, ...]  # Pergunta

# 4. Calcula similaridade (cosseno) entre query e CADA produto
scores = []

for product_vector in product_vectors:
    score = cosine_similarity(query_vector, product_vector)
    scores.append(score)

# Resultado:
# scores = [0.92, 0.15, 0.10, ...]
#          ↑     ↑     ↑
#          Cam   Calça Tênis
```

### 📐 MATEMÁTICA: SIMILARIDADE DO COSSENO

```python
def cosine_similarity(A, B):
    """
    Mede o ângulo entre dois vetores
    Resultado: -1 a 1
    - 1.0 = vetores idênticos (mesmo significado)
    - 0.0 = vetores perpendiculares (sem relação)
    """
    dot_product = sum(a * b for a, b in zip(A, B))
    magnitude_A = sqrt(sum(a**2 for a in A))
    magnitude_B = sqrt(sum(b**2 for b in B))
    
    return dot_product / (magnitude_A * magnitude_B)
```

**Visualização geométrica (simplificada para 2D):**

```
         Camiseta (0.92) ✅
              •
             /
            / ← ângulo pequeno
           /
    Consulta •
          \
           \
            \ ← ângulo grande
             \
              •
            Tênis (0.10) ❌
```

---

#### **Passo 3.3: ORDENAR E RETORNAR TOP-5**

```python
# 5. Ordena por score (maior primeiro)
resultados = sorted(zip(ids, scores), key=lambda x: x[1], reverse=True)

# 6. Pega top-5
top5 = resultados[:5]

# Resultado:
[
    (1, 0.92),  # ID 1: Camiseta Básica - score alto!
    (9, 0.85),  # ID 9: Camiseta Estampada
    (14, 0.78), # ID 14: Camiseta Polo
    (2, 0.15),  # ID 2: Calça Jeans - score baixo
    (3, 0.10),  # ID 3: Tênis - score baixo
]

# 7. Carrega dados completos do catalogo.pkl
produtos_retornados = []
for product_id, score in top5:
    produto = catalogo[product_id]
    produto['score'] = score
    produtos_retornados.append(produto)
```

---

## 🎯 RESUMO DO FLUXO COMPLETO

```
FASE 1: PREPARAÇÃO (você roda 1x)
===================================

adicionar_produtos.py
    ↓ (SQL INSERT)
PostgreSQL/SQLite
    ↓ (SQL SELECT)
popular_embeddings.py
    ↓ (HTTP para AWS)
AWS Bedrock Titan
    ↓ (Retorna vetores)
Salva em:
    ├── catalogo.pkl (dados dos produtos)
    └── vectors.pkl  (embeddings)


FASE 2: CONSULTA (cada vez que usuário pergunta)
=================================================

Usuário: "camiseta confortável"
    ↓ (normaliza)
"camiseta confortavel"
    ↓ (HTTP para AWS)
AWS Bedrock Titan
    ↓ (Retorna vetor da query)
[0.240, -0.130, 0.895, ...]
    ↓ (carrega vectors.pkl)
Compara com 43 produtos
    ↓ (cosine similarity)
Scores: [0.92, 0.85, 0.78, 0.15, 0.10, ...]
    ↓ (ordena e pega top-5)
Top-5 produtos
    ↓ (carrega catalogo.pkl)
Produtos completos com scores
    ↓ (formata contexto)
Augmenter
    ↓ (envia para AWS)
Claude no Bedrock
    ↓
Resposta em linguagem natural
```

---

## 💾 ARQUIVOS GERADOS

### `db_data/catalogo.pkl`
```python
{
    1: {
        'id': 1,
        'nome': 'Camiseta Básica',
        'preco': 39.90,
        # ... todos os campos
    },
    # ... 43 produtos
}
```
**Tamanho:** ~100 KB  
**Função:** Dados completos dos produtos

---

### `db_data/vectors.pkl`
```python
{
    'ids': [1, 2, 3, ..., 43],
    'vectors': array([
        [0.234, -0.127, 0.891, ...],  # 1024 números
        # ... 43 linhas
    ])
}
```
**Tamanho:** ~500 KB  
**Função:** Embeddings para busca vetorial

---

## 🔑 CONCEITOS-CHAVE

### 1. **Embedding = Representação Matemática do Significado**

```
Texto: "camiseta confortável"
    ↓ [Titan Embeddings]
Vetor: [0.24, -0.13, 0.89, ..., -0.32]
       ↑
    Captura o "significado"
```

### 2. **Similaridade do Cosseno = Medida de Proximidade**

```
Quanto menor o ângulo entre vetores,
mais similares são os significados!

Camiseta & "camiseta confortável" → ângulo pequeno → score alto (0.92)
Tênis & "camiseta confortável"    → ângulo grande  → score baixo (0.10)
```

### 3. **Por que isso funciona?**

Porque o modelo Titan foi treinado em bilhões de textos e aprendeu que:
- "camiseta" e "blusa" são similares
- "confortável" e "macio" são similares
- "camiseta" e "notebook" NÃO são similares

---

## ⚡ POR QUE PRECISA REGENERAR EMBEDDINGS?

```
❌ SE NÃO REGENERAR:

Adiciona produtos no banco
    ↓
vectors.pkl ainda tem apenas 5 produtos antigos
    ↓
RAG só encontra os 5 antigos
    ↓
Novos produtos INVISÍVEIS para busca!


✅ SE REGENERAR:

Adiciona produtos no banco (43 produtos)
    ↓
Roda popular_embeddings --force
    ↓
vectors.pkl agora tem 43 produtos
    ↓
RAG encontra TODOS os 43!
```

---

## 🎬 RESUMÃO FINAL

**INPUTAR CONHECIMENTO = 2 PASSOS:**

1. **Adicionar dados no banco** (SQL INSERT)
2. **Gerar embeddings** (AWS Bedrock + salvar em pickle)

**RESULTADO:**
- Sistema consegue fazer busca SEMÂNTICA
- Encontra produtos por significado, não apenas por palavras exatas
- "camiseta confortável" encontra produtos mesmo que não tenham exatamente essas palavras

**Entendeu como funciona?** 🚀