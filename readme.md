# Criar o ambiente virtual
python -m venv venv

# Ativar o ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

pip install django

django-admin startproject my_project_ia_rag_aws 

cd my_project_ia_rag_aws 

python manage.py runserver

python manage.py migrate

python manage.py runserver

python manage.py createsuperuser

admin
admin

python manage.py startapp meu_app_rag

python manage.py makemigrations
python manage.py migrate

----# 1. Migrações
python manage.py makemigrations
python manage.py migrate

# 2. Criar superusuário
python manage.py createsuperuser

# 3. Adicionar produtos (via shell)
python manage.py shell
# (cole o código dos produtos)

# 4. Gerar embeddings (OBRIGATÓRIO!)
python manage.py popular_embeddings

# 5. Rodar servidor
python manage.py runserver

# 6. Testar no navegador
# http://127.0.0.1:8000/api/docs/

---

(venv) PS C:\projects-github\django-rag-langhain-aws\my_project_ia_rag_aws> python manage.py popular_embeddings

=== GERADOR DE EMBEDDINGS RAG ===


📦 Exportando catálogo...
✔ 5 produtos exportados

🧠 Gerando embeddings...
  [1/5] ✔ Embedding gerado para ID=5: Óculos de Sol Aviador
  [2/5] ✔ Embedding gerado para ID=4: Camiseta Básica Algodão
  [3/5] ✔ Embedding gerado para ID=3: Tênis Corrida Pro Run
  [4/5] ✔ Embedding gerado para ID=2: Sandália Rasteira Dourada
  [5/5] ✔ Embedding gerado para ID=1: Sandália Feminina Conforto

✔ 5 embeddings salvos

✅ Processo concluído!
Arquivos gerados:
  - C:\projects-github\django-rag-langhain-aws\my_project_ia_rag_aws\db_data\catalogo.pkl
  - C:\projects-github\django-rag-langhain-aws\my_project_ia_rag_aws\db_data\vectors.pkl

(venv) PS C:\projects-github\django-rag-langhain-aws\my_project_ia_rag_aws> 