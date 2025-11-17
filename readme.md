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