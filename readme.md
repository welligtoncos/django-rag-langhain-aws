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

pip install djangorestframework