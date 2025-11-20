# Build e iniciar em modo desenvolvimento

# Pare tudo
docker-compose -f docker-compose.dev.yml down

# Inicie novamente
docker-compose -f docker-compose.dev.yml up

# Frontend: http://localhost:4200
# Backend: http://localhost:8000


----------------------------------------------------
# Build e iniciar em modo produção
docker-compose up --build -d

# Frontend: http://localhost
# Backend: http://localhost:8000

# Ver logs
docker-compose logs -f

# Parar containers
docker-compose down

# Build e iniciar em modo produção
docker-compose up --build -d

# Frontend: http://localhost
# Backend: http://localhost:8000

# Ver logs
docker-compose logs -f

# Parar containers
docker-compose down

--------------------------------------------------------------------------

# Rebuild apenas o frontend
docker-compose build frontend

# Entrar no container
docker exec -it angular_frontend sh

# Ver logs de um serviço específico
docker-compose logs -f frontend
```

## Estrutura Final:
```
django-rag-langhain-aws/
├── backend-django/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── requirements.txt
│   └── manage.py
├── frontend-angular/
│   └── frontend_ia_rag_aws/
│       ├── Dockerfile
│       ├── .dockerignore
│       ├── nginx.conf
│       └── package.json
├── docker-compose.yml
├── docker-compose.dev.yml
└── package.json (opcional)

--------------------------------------------------
# Ver logs em tempo real
docker-compose -f docker-compose.dev.yml logs -f

# Parar os containers
docker-compose -f docker-compose.dev.yml down

# Reiniciar
docker-compose -f docker-compose.dev.yml restart

# Ver containers rodando
docker ps
--------------------------------------------------- 
# Subir em produção:

docker-compose up -d

------

# 1. Ver o que tem de diferente
git status

# 2. Buscar updates do repositório remoto
git fetch origin

# 3. Resetar para o origin/main (descarta mudanças locais)
git reset --hard origin/main

# 4. Limpar arquivos não rastreados (se necessário)
git clean -fd

# 5. Confirmar que está atualizado
git status

---

docker-compose -f docker-compose.dev.yml up -d
# Acesso: http://54.163.220.235:4200
# Precisa ter: apiUrl: 'http://54.163.220.235:8000/api' no environment.development.ts


docker-compose up -d
# Acesso: http://54.163.220.235



O erro 503 – Serviço RAG indisponível está claríssimo no log do backend:

❌ Arquivo /app/my_project_ia_rag_aws/db_data/vectors.pkl não encontrado.
Execute: python manage.py popular_embeddings --force


👉 Isso significa que o backend está funcionando, mas o RAG não tem embeddings carregados, então ele trava e retorna 503.

✅ Como resolver (Local / Docker)
✔️ 1. Acesse o container do backend

No terminal:

docker exec -it django_backend_dev bash

✔️ 2. Gere os embeddings

No container, rode:

python manage.py popular_embeddings --force


Isso vai:

ler sua base de produtos

criar vectors.pkl

salvar em /app/my_project_ia_rag_aws/db_data/

Se tudo der certo, você verá algo como:

✔️ Embeddings criados com sucesso!

✔️ 3. Reinicie o backend

Ainda no host:

docker compose restart backend