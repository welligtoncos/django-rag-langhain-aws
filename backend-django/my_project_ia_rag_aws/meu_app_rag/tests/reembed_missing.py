import os, sys, django
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project_ia_rag_aws.settings")
django.setup()

from meu_app_rag.models import Documento
from meu_app_rag.rag.embeddings import Embeddings

embeddings = Embeddings()

qs = Documento.objects.filter(status="ativo", embedding__isnull=True)
print("ativos sem embedding:", qs.count())

for doc in qs.iterator():
    emb = embeddings.embed(doc.conteudo)
    doc.embedding = emb.tolist() if hasattr(emb, "tolist") else list(emb)
    doc.save(update_fields=["embedding"])
    print("re-embedded:", doc.id, doc.titulo, "len=", len(doc.embedding))
