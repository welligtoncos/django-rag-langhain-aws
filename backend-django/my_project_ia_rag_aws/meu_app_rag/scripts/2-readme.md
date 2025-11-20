# 1. Gerar embeddings
python manage.py popular_embeddings --force

# 2. Ver no banco
python manage.py shell
>>> from meu_app_rag.models import Produto
>>> Produto.objects.count()
10
>>> Produto.objects.first()
<Produto: Camiseta Básica Branca - R$ 39.90>

# 3. Testar API
curl http://localhost:8000/api/rag/stats/

# 4. Testar RAG
curl -X POST http://localhost:8000/api/rag/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "camiseta branca", "limit": 5}'