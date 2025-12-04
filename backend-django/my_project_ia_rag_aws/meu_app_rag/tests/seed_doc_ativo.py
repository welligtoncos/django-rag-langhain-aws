import os, sys, django, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project_ia_rag_aws.settings")
django.setup()

from meu_app_rag.models import KnowledgeBase, Documento

class FakeEmbeddings:
    def embed(self, text: str):
        h = hashlib.sha256(text.encode("utf-8")).digest()
        return [b / 255.0 for b in h] * 2  # 64

def main():
    base = KnowledgeBase.objects.order_by("id").first()
    doc = Documento.objects.create(
        base=base,
        titulo="Batismo - Documentos necessários",
        slug="batismo-documentos",
        conteudo="Para batizar a criança: certidão de nascimento, RG dos pais, e curso.",
        status="ativo",
        versao=1,
    )
    doc.embedding = FakeEmbeddings().embed(doc.titulo + "\n" + doc.conteudo)
    doc.save(update_fields=["embedding"])
    print("Criado doc ativo com embedding:", doc.id)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
