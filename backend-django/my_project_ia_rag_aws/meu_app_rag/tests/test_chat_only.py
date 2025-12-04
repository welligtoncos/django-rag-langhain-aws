import os, sys, django
from pathlib import Path
from django.db.models import Q

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project_ia_rag_aws.settings")
django.setup()

from meu_app_rag.models import Documento, KnowledgeBase

def main():
    print("=== DIAGNÓSTICO RETRIEVER ===")

    print("Bases:", KnowledgeBase.objects.count())
    print("Docs total:", Documento.objects.count())
    print("Docs status=ativo:", Documento.objects.filter(status="ativo").count())

    # embedding pode ser NULL ou lista vazia
    try:
        sem_emb = Documento.objects.filter(Q(embedding__isnull=True) | Q(embedding=[])).count()
    except Exception:
        sem_emb = Documento.objects.filter(embedding__isnull=True).count()

    print("Docs sem embedding:", sem_emb)

    # Mostra 5 docs e seus status/slugs
    for d in Documento.objects.all().order_by("-id")[:5]:
        emb_ok = bool(getattr(d, "embedding", None))
        print(f"- id={d.id} base={d.base_id} status={d.status} slug={d.slug} emb={'OK' if emb_ok else 'X'}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
