# 🔍 SELECT - POR QUE LER TODOS OS PRODUTOS?

---

## 🎯 QUANDO ACONTECE O SELECT

```bash
# Você executa este comando:
python manage.py popular_embeddings --force
```

**Dentro do arquivo `popular_embeddings.py`:**

```python
def exportar_catalogo(self):
    """Exporta produtos do banco para arquivo pickle"""
    
    # 🔴 AQUI ACONTECE O SQL SELECT!
    produtos = Produto.objects.all()
    #          ↑
    #    Isso executa: SELECT * FROM meu_app_rag_produto
```

---

## 📊 O QUE ESSE SELECT RETORNA

### **SQL executado:**
```sql
SELECT 
    id,
    nome,
    categoria,
    subcategoria,
    preco,
    preco_promocional,
    marca,
    cor,
    tamanho,
    material,
    estoque,
    descricao,
    especificacoes,
    avaliacao,
    num_avaliacoes,
    peso,
    dimensoes
FROM meu_app_rag_produto;
```

### **Retorna TODOS os produtos:**

```
Resultado do SELECT:
┌────┬─────────────────┬───────────┬────────┬─────────────────────────────┐
│ ID │ Nome            │ Categoria │ Preço  │ Descrição                   │
├────┼─────────────────┼───────────┼────────┼─────────────────────────────┤
│ 1  │ Camiseta Básica │ Roupas    │ 39.90  │ Camiseta de algodão...      │
│ 2  │ Calça Jeans     │ Roupas    │ 149.90 │ Calça jeans skinny...       │
│ 3  │ Tênis Corrida   │ Calçados  │ 199.90 │ Tênis para corrida...       │
│ 4  │ Smartwatch      │ Eletrôn.  │ 599.90 │ Relógio inteligente...      │
│ .. │ ...             │ ...       │ ...    │ ...                         │
│ 43 │ Suéter Gola V   │ Roupas    │ 99.90  │ Suéter clássico...          │
└────┴─────────────────┴───────────┴────────┴─────────────────────────────┘

Total: 43 linhas (todos os produtos)
```

---

## 🤔 POR QUE LER **TODOS**?

### **Porque você precisa gerar embedding para CADA produto!**

```
Produto 1 → Precisa de embedding
Produto 2 → Precisa de embedding
Produto 3 → Precisa de embedding
...
Produto 43 → Precisa de embedding

❌ Não dá para pular nenhum!
```

---

## 📝 O QUE ACONTECE DEPOIS DO SELECT (Passo a Passo)

### **Passo 1: SELECT traz todos os dados**

```python
# popular_embeddings.py

produtos = Produto.objects.all()  # ← SQL SELECT

# Variável 'produtos' agora contém:
# [
#   <Produto: Camiseta Básica>,
#   <Produto: Calça Jeans>,
#   <Produto: Tênis Corrida>,
#   ... 43 objetos
# ]
```

---

### **Passo 2: Transformar em dicionário Python**

```python
catalogo = {}

for p in produtos:  # Para cada produto retornado pelo SELECT
    catalogo[p.id] = {
        'id': p.id,
        'nome': p.nome,
        'categoria': p.categoria,
        'preco': float(p.preco),
        'descricao': p.descricao,
        # ... todos os campos
    }

# Resultado:
# catalogo = {
#     1: {'id': 1, 'nome': 'Camiseta Básica', 'preco': 39.90, ...},
#     2: {'id': 2, 'nome': 'Calça Jeans', 'preco': 149.90, ...},
#     3: {'id': 3, 'nome': 'Tênis Corrida', 'preco': 199.90, ...},
#     ... 43 produtos
# }
```

---

### **Passo 3: Salvar em arquivo pickle (catalogo.pkl)**

```python
with open('db_data/catalogo.pkl', 'wb') as f:
    pickle.dump(catalogo, f)

# Agora existe o arquivo catalogo.pkl com TODOS os dados
```

---

### **Passo 4: Gerar embeddings para CADA produto**

```python
for pid, produto in catalogo.items():
    # Criar texto descritivo
    texto = f"{produto['nome']}. {produto['descricao']}. Categoria: {produto['categoria']}"
    
    # Exemplo para Produto 1:
    # texto = "Camiseta Básica. Camiseta de algodão. Categoria: Roupas"
    
    # Normalizar
    texto_norm = unidecode(texto.lower())
    # "camiseta basica. camiseta de algodao. categoria: roupas"
    
    # 🌐 ENVIAR PARA AWS BEDROCK (1 requisição por produto)
    vetor = embeddings.embed(texto_norm)
    
    # Retorna vetor de 1024 números:
    # [0.234, -0.127, 0.891, ..., -0.321]
    
    # Guardar
    ids.append(pid)
    vectors.append(vetor)
```

**Isso acontece 43 VEZES (uma para cada produto)!**

```
Produto 1 → AWS Bedrock → Vetor 1
Produto 2 → AWS Bedrock → Vetor 2
Produto 3 → AWS Bedrock → Vetor 3
...
Produto 43 → AWS Bedrock → Vetor 43
```

---

### **Passo 5: Salvar todos os vetores (vectors.pkl)**

```python
with open('db_data/vectors.pkl', 'wb') as f:
    pickle.dump({
        'ids': [1, 2, 3, ..., 43],
        'vectors': np.array([
            [0.234, -0.127, ...],  # Vetor do produto 1
            [0.198, -0.115, ...],  # Vetor do produto 2
            [0.050, 0.230, ...],   # Vetor do produto 3
            # ... 43 vetores
        ])
    }, f)
```

---

## 🎨 ANALOGIA: TIRAR FOTO 3x4 DE TODOS

Imagine que você precisa fazer um catálogo de identificação:

```
┌────────────────────────────────────────┐
│ FASE 1: CHAMAR TODOS (SELECT)         │
├────────────────────────────────────────┤
│ Professor: "Todos os alunos venham!"   │
│                                        │
│ SQL: SELECT * FROM alunos              │
│                                        │
│ Resultado: 43 alunos na sala           │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ FASE 2: TIRAR FOTO DE CADA UM         │
├────────────────────────────────────────┤
│ 📸 Aluno 1 - CLIQUE!                   │
│ 📸 Aluno 2 - CLIQUE!                   │
│ 📸 Aluno 3 - CLIQUE!                   │
│ ...                                    │
│ 📸 Aluno 43 - CLIQUE!                  │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ FASE 3: MONTAR ÁLBUM                  │
├────────────────────────────────────────┤
│ Álbum com 43 fotos                     │
│ (vectors.pkl)                          │
└────────────────────────────────────────┘
```

**Por que chamar TODOS de uma vez?**
- ✅ Mais eficiente
- ✅ Garante que ninguém fica de fora
- ✅ Todas as fotos do mesmo dia/momento

---

## 🔄 FLUXO DETALHADO COM TEMPOS

```
python manage.py popular_embeddings --force

┌─────────────────────────────────────────┐
│ 1. SELECT * FROM produtos               │
│    ⏱️ Tempo: ~50ms                      │
│    📦 Resultado: 43 produtos            │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ 2. Transformar em dicionário Python     │
│    ⏱️ Tempo: ~1ms                       │
│    💾 Memória: ~50KB                    │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ 3. Salvar catalogo.pkl                  │
│    ⏱️ Tempo: ~10ms                      │
│    💾 Arquivo: ~100KB                   │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ 4. Gerar embeddings (AWS Bedrock)       │
│    Para cada produto:                   │
│    ├─ Produto 1 → AWS → Vetor (~300ms) │
│    ├─ Produto 2 → AWS → Vetor (~300ms) │
│    ├─ Produto 3 → AWS → Vetor (~300ms) │
│    └─ ... 43x                           │
│    ⏱️ Tempo total: ~13 segundos         │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ 5. Salvar vectors.pkl                   │
│    ⏱️ Tempo: ~50ms                      │
│    💾 Arquivo: ~500KB                   │
└─────────────────────────────────────────┘
              ↓
        ✅ PRONTO!
```

---

## 💡 POR QUE NÃO LER 1 POR VEZ?

### **❌ Jeito RUIM (ler 1 por vez):**

```python
# Para cada busca do usuário, fazer:

# SQL 1
produto1 = Produto.objects.get(id=1)
embedding1 = gerar_embedding(produto1)

# SQL 2
produto2 = Produto.objects.get(id=2)
embedding2 = gerar_embedding(produto2)

# ... 43 queries SQL
# ... 43 chamadas AWS

# PROBLEMA: Muito lento e ineficiente!
```

### **✅ Jeito BOM (ler tudo de uma vez):**

```python
# 1 SQL apenas
produtos = Produto.objects.all()  # SELECT *

# Processa em lote
for produto in produtos:
    embedding = gerar_embedding(produto)

# VANTAGEM: 1 query SQL, processa tudo
```

---

## 🎯 EXEMPLO REAL COM 3 PRODUTOS

### **Banco de Dados:**
```
┌────┬─────────────┬──────────┬────────┐
│ ID │ Nome        │ Categoria│ Preço  │
├────┼─────────────┼──────────┼────────┤
│ 1  │ Camiseta    │ Roupas   │ 39.90  │
│ 2  │ Calça       │ Roupas   │ 149.90 │
│ 3  │ Tênis       │ Calçados │ 199.90 │
└────┴─────────────┴──────────┴────────┘
```

### **SQL executado:**
```sql
SELECT * FROM meu_app_rag_produto;
```

### **Retorno do SELECT:**
```python
[
    <Produto: id=1, nome="Camiseta", preco=39.90>,
    <Produto: id=2, nome="Calça", preco=149.90>,
    <Produto: id=3, nome="Tênis", preco=199.90>
]
```

### **Transformação em dicionário:**
```python
{
    1: {
        'id': 1,
        'nome': 'Camiseta',
        'categoria': 'Roupas',
        'preco': 39.90,
        'descricao': '...'
    },
    2: {
        'id': 2,
        'nome': 'Calça',
        'categoria': 'Roupas',
        'preco': 149.90,
        'descricao': '...'
    },
    3: {
        'id': 3,
        'nome': 'Tênis',
        'categoria': 'Calçados',
        'preco': 199.90,
        'descricao': '...'
    }
}
```

### **Geração de embeddings:**
```python
# Produto 1
texto = "Camiseta. Camiseta de algodão. Categoria: Roupas"
vetor1 = AWS_Bedrock(texto)  # [0.2, -0.1, 0.8, ...]

# Produto 2
texto = "Calça. Calça jeans skinny. Categoria: Roupas"
vetor2 = AWS_Bedrock(texto)  # [0.1, 0.9, -0.2, ...]

# Produto 3
texto = "Tênis. Tênis para corrida. Categoria: Calçados"
vetor3 = AWS_Bedrock(texto)  # [0.05, 0.2, -0.4, ...]
```

### **Resultado final (vectors.pkl):**
```python
{
    'ids': [1, 2, 3],
    'vectors': [
        [0.2, -0.1, 0.8, ...],   # Camiseta
        [0.1, 0.9, -0.2, ...],   # Calça
        [0.05, 0.2, -0.4, ...]   # Tênis
    ]
}
```

---

## 📊 COMPARAÇÃO: SELECT vs GET INDIVIDUAL

| Operação | Queries SQL | Tempo | Eficiência |
|----------|-------------|-------|------------|
| `SELECT *` | 1 | ~50ms | ✅ Excelente |
| `GET` individual 43x | 43 | ~2150ms | ❌ Ruim |

---

## 🔑 RESUMO

### **O SELECT faz:**
1. ✅ Busca **TODOS** os produtos de uma vez
2. ✅ Traz **TODOS** os campos de cada produto
3. ✅ Retorna 43 linhas (43 produtos)

### **Por que TODOS?**
- Precisa gerar embedding para cada um
- Não dá para pular nenhum
- Mais eficiente fazer 1 query grande do que 43 pequenas

### **O que acontece depois?**
1. Transforma em dicionário Python
2. Salva em `catalogo.pkl`
3. Gera embedding para cada um (AWS)
4. Salva embeddings em `vectors.pkl`

### **E depois disso?**
- SQL não é mais usado!
- Tudo fica em arquivos pickle
- Buscas usam memória RAM (super rápido)

---

**RESUMINDO EM 1 FRASE:**

**"O SELECT pega TODOS os produtos do banco DE UMA VEZ para poder gerar os embeddings de CADA UM e salvar em arquivos que serão usados nas buscas (sem precisar de SQL novamente)."**

🎯