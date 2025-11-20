import os
import sys
import django

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project_ia_rag_aws.settings')
django.setup()

from meu_app_rag.models import Produto

print("🗑️  RESETANDO BANCO DE DADOS...")
print(f"Total de produtos antes: {Produto.objects.count()}")

# Deletar todos
Produto.objects.all().delete()

print(f"✅ Banco resetado! Total agora: {Produto.objects.count()}")