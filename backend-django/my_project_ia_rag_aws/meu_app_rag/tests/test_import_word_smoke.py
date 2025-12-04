import os, sys, django
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project_ia_rag_aws.settings")
django.setup()

from meu_app_rag.importers.word_importer import WordImporter
from meu_app_rag.models import KnowledgeBase

def main():
    base, _ = KnowledgeBase.objects.get_or_create(
        slug="eventos",
        defaults={
            "nome": "Eventos",
            "descricao": "Base Eventos",
            "tipo": "atualizavel",
            "ativo": True,
        },
    )

    
    # ALTERA AQUI
    caminho = r"C:\temp\teste_import_batismo.docx"

    doc = WordImporter().processar_word(caminho, base_slug=base.slug)

    print("✅ Importado!")
    print("id:", doc.id)
    print("titulo:", doc.titulo)
    print("categoria:", doc.categoria)
    print("tags:", doc.tags)
    print("status:", doc.status)
    print("tem_embedding:", doc.embedding is not None)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
