import os, sys, django
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project_ia_rag_aws.settings")
django.setup()

from meu_app_rag.models import Documento, KnowledgeBase

def emb_len(e):
    if not e: return None
    try: return len(e)
    except: return "??"

print("Bases:")
for b in KnowledgeBase.objects.all().order_by("id"):
    total = b.documentos.count()
    ativos = b.documentos.filter(status="ativo").count()
    print(f"- {b.id} {b.slug}: total={total} ativos={ativos}")

print("\nDocs ativos:")
qs = Documento.objects.filter(status="ativo")
print("ativos:", qs.count())
for d in qs.order_by("-id")[:20]:
    print(f"- id={d.id} base={d.base_id} titulo={d.titulo} emb_len={emb_len(d.embedding)}")