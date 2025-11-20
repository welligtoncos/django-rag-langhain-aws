# 1. Salvar o script
# scripts/popular_100_produtos.py

# 2. Executar
cd backend-django/my_project_ia_rag_aws
python scripts/popular_100_produtos.py

# 3. Aguardar (leva ~2 minutos)

# 4. Gerar embeddings
python manage.py popular_embeddings --force

# 5. Testar
python manage.py runserver
```

---

## 📊 RESUMO DOS 100 PRODUTOS
```
✅ Roupas Masculinas:    15 produtos
✅ Roupas Femininas:     15 produtos
✅ Calçados:             15 produtos
✅ Eletrônicos:          10 produtos
✅ Acessórios:           10 produtos
✅ Beleza:               10 produtos
✅ Móveis:                5 produtos
✅ Casa & Decoração:      5 produtos
✅ Livros & Papelaria:    5 produtos
✅ Diversos:             10 produtos

TOTAL: 100 produtos