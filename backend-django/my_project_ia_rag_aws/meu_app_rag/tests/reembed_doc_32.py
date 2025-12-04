import os, sys, django
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project_ia_rag_aws.settings")
django.setup()

from meu_app_rag.models import Documento
from meu_app_rag.rag.embeddings import Embeddings

doc_id = 32

doc = Documento.objects.get(id=doc_id)

emb = Embeddings().embed(doc.conteudo)
# se seu model salva JSON, converte pra list
doc.embedding = emb.tolist() if hasattr(emb, "tolist") else list(emb)
doc.save(update_fields=["embedding"])

print("OK:", doc.id, "embedding_len=", len(doc.embedding))
