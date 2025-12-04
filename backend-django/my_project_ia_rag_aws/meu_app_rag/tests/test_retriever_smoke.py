import os, sys, django, hashlib
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project_ia_rag_aws.settings")
django.setup()

from meu_app_rag.rag.retriever import MultiBaseRetriever
from meu_app_rag.models import Documento


class FakeEmbeddings:
    """
    Fake determinístico que gera embeddings com a MESMA dimensão dos embeddings já salvos no banco.
    Assim evita mismatch (ex.: 64 vs 1024).
    """
    def __init__(self, dim: int):
        self.dim = dim

    def embed(self, text: str):
        vals = []
        counter = 0
        while len(vals) < self.dim:
            h = hashlib.sha256(f"{text}|{counter}".encode("utf-8")).digest()  # 32 bytes
            vals.extend([b / 255.0 for b in h])
            counter += 1
        return vals[:self.dim]


def main():
    pergunta = "batismo criança documentos"

    # Inferir dimensão diretamente do banco (recomendado)
    amostra = (
        Documento.objects
        .filter(status="ativo")
        .exclude(embedding__isnull=True)
        .first()
    )
    if not amostra or not amostra.embedding:
        print("Não há documentos ativos com embedding no banco para testar.")
        return 1

    dim_banco = len(amostra.embedding)

    retriever = MultiBaseRetriever()
    retriever.embeddings = FakeEmbeddings(dim=dim_banco)

    resultados = retriever.retrieve(query=pergunta, limit=5)

    print("\n=== RESULTADOS retrieve() ===")
    print("Pergunta:", pergunta)
    print("Dimensão do embedding (banco):", dim_banco)
    print("Dimensão do embedding (query fake):", len(retriever.embeddings.embed(pergunta)))
    print("Docs ativos c/ embedding:",
          Documento.objects.filter(status="ativo").exclude(embedding__isnull=True).count())

    print("Retornados:", len(resultados))
    for i, r in enumerate(resultados, 1):
        print(f"{i}. titulo={r.get('titulo')} score={r.get('score')} id={r.get('id')} base={r.get('base_id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
