import os
import sys
import django
from pathlib import Path
import hashlib
import uuid
from datetime import datetime

# -----------------------------------------------------------------------------
# Django setup (rodar de qualquer lugar)
# -----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]  # .../my_project_ia_rag_aws
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project_ia_rag_aws.settings")
django.setup()

from meu_app_rag.rag.manager import KnowledgeManager
from meu_app_rag.rag.retriever import MultiBaseRetriever
from meu_app_rag.rag.augmenter import ContextAugmenter
from meu_app_rag.models import KnowledgeBase, Documento


RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]


# =========================
# Fake embeddings (sem Bedrock)
# =========================
class FakeEmbeddings:
    def embed(self, text: str):
        h = hashlib.sha256(text.encode("utf-8")).digest()
        v = [b / 255.0 for b in h]   # 32 dims
        return v + v                 # 64 dims


def patch_offline_embeddings():
    """
    Faz o retriever usar embeddings fake sem chamar AWS/Bedrock.
    """
    fake = FakeEmbeddings()
    orig_init = MultiBaseRetriever.__init__

    def new_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self.embeddings = fake

    MultiBaseRetriever.__init__ = new_init
    return fake


FAKE = patch_offline_embeddings()


# =========================
# Helpers
# =========================
def ensure_base():
    base, _ = KnowledgeBase.objects.get_or_create(
        slug="teste-suite",
        defaults=dict(
            nome="Base Teste Suite",
            tipo="estatico",
            descricao="Base para testes automatizados",
            icone="🧪",
            prioridade=999,
            cor="#00AAFF",
        ),
    )
    return base


def ensure_document_is_valid_for_retrieval(doc: Documento):
    """
    Alguns retrievers filtram por flags/data. Se esses campos existirem no seu model,
    a gente garante que estão em estado "válido".
    """
    changed = False
    for field, value in [
        ("ativo", True),
        ("publicado", True),
        ("data_inicio", None),
        ("data_fim", None),
    ]:
        if hasattr(doc, field):
            current = getattr(doc, field)
            if current != value:
                setattr(doc, field, value)
                changed = True

    if changed:
        doc.save()
    return doc


def ensure_document_has_embedding(doc: Documento, text_for_embedding: str):
    if getattr(doc, "embedding", None):
        return doc

    doc.embedding = FAKE.embed(text_for_embedding)
    try:
        doc.save(update_fields=["embedding"])
    except Exception:
        doc.save()
    return doc


def safe_delete(obj):
    try:
        if obj:
            obj.delete()
    except Exception:
        pass


# =========================
# Tests
# =========================
def test_setup():
    print("1️⃣ Testando setup básico...")
    bases = KnowledgeBase.objects.count()
    docs = Documento.objects.count()

    print(f"   ✅ Bases: {bases}")
    print(f"   ✅ Documentos: {docs}")

    ensure_base()
    return True


def test_embeddings():
    print("\n2️⃣ Testando embeddings (offline)...")
    try:
        vetor = FAKE.embed("teste")
        print(f"   ✅ Embedding gerado: {len(vetor)} dimensões")
        return len(vetor) == 64
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False


def test_manager():
    print("\n3️⃣ Testando KnowledgeManager (offline)...")
    base = ensure_base()
    manager = KnowledgeManager()

    doc = None
    try:
        doc = manager.adicionar_documento(
            base=base,
            titulo=f"Teste Automatizado [{RUN_ID}]",
            conteudo="Este é um documento de teste " * 10,
            categoria="Teste",
            tags=["teste", "automatizado"],
            gerar_embedding=False,  # offline
        )

        ensure_document_is_valid_for_retrieval(doc)
        ensure_document_has_embedding(doc, "documento teste automatizado")

        print(f"   ✅ Documento criado: ID {doc.id}")
        print(f"   ✅ Embedding: {'Sim' if doc.embedding else 'Não'}")
        return bool(doc.embedding)
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    finally:
        safe_delete(doc)


def test_retrieval():
    print("\n4️⃣ Testando retrieval (offline)...")
    base = ensure_base()
    manager = KnowledgeManager()
    retriever = MultiBaseRetriever()

    doc = None
    try:
        doc = manager.adicionar_documento(
            base=base,
            titulo=f"Teste Busca Vetorial [{RUN_ID}]",
            conteudo="Como faço para batizar meu filho na paróquia?",
            gerar_embedding=False,
        )

        ensure_document_is_valid_for_retrieval(doc)
        ensure_document_has_embedding(doc, "batismo criança paróquia")

        resultados = retriever.retrieve(query="batismo de criança", limit=5)

        print(f"   ✅ Documentos encontrados: {len(resultados)}")
        if resultados:
            print(f"   ✅ Melhor match: {resultados[0].get('titulo')}")
            if "score" in resultados[0]:
                print(f"   ✅ Score: {resultados[0]['score']:.4f}")

        return len(resultados) > 0
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    finally:
        safe_delete(doc)


def test_rag_complete():
    print("\n5️⃣ Testando RAG completo (offline, sem geração)...")
    base = ensure_base()
    manager = KnowledgeManager()
    doc = None

    try:
        doc = manager.adicionar_documento(
            base=base,
            titulo=f"Informações sobre Batismo [{RUN_ID}]",
            conteudo=(
                "# BATISMO\n\n"
                "Para batizar seu filho, você precisa:\n"
                "- Certidão de nascimento\n"
                "- RG dos pais\n"
                "- Curso de preparação (obrigatório)\n\n"
                "O agendamento deve ser feito com 45 dias de antecedência.\n"
                "Telefone: (11) 1234-5678\n"
            ),
            gerar_embedding=False,
        )

        ensure_document_is_valid_for_retrieval(doc)
        ensure_document_has_embedding(doc, "batismo certidão rg curso 45 dias telefone")

        retriever = MultiBaseRetriever()
        documentos = retriever.retrieve(query="como batizar criança", limit=3)
        print(f"   ✅ Retrieval: {len(documentos)} docs")

        augmenter = ContextAugmenter()
        contexto = augmenter.augment("como batizar criança", documentos)
        print(f"   ✅ Augmentation: {len(contexto)} chars")

        print("   ⏭️  Generation: pulado (offline/sem API)")
        return len(documentos) > 0 and len(contexto) > 0
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    finally:
        safe_delete(doc)


def test_versioning():
    print("\n6️⃣ Testando versionamento...")
    base = ensure_base()
    manager = KnowledgeManager()

    doc_v1 = None
    doc_v2 = None

    try:
        # tenta algumas vezes caso o slug gerado internamente colida
        for attempt in range(5):
            try:
                titulo = f"Doc Versionado [{RUN_ID}] attempt={attempt}"
                doc_v1 = manager.adicionar_documento(
                    base=base,
                    titulo=titulo,
                    conteudo="Versão 1 - conteúdo inicial (>= 10 chars)",
                    gerar_embedding=False,
                )
                break
            except Exception as e:
                # colisão comum: UNIQUE(base_id, slug)
                doc_v1 = None
                if "UNIQUE" in str(e).upper():
                    continue
                raise

        if not doc_v1:
            raise RuntimeError("Não foi possível criar doc_v1 sem colidir slug.")

        doc_v2 = manager.atualizar_documento(
            documento_id=doc_v1.id,
            conteudo="Versão 2 - conteúdo atualizado (>= 10 chars)",
        )

        ok_link = bool(getattr(doc_v2, "documento_anterior_id", None)) and (doc_v2.documento_anterior_id == doc_v1.id)
        print(f"   ✅ v1 criada: ID {doc_v1.id} | titulo={doc_v1.titulo} | slug={getattr(doc_v1, 'slug', '-')}")
        print(f"   ✅ v2 criada: ID {doc_v2.id} | titulo={doc_v2.titulo} | slug={getattr(doc_v2, 'slug', '-')}")
        print(f"   ✅ v2 aponta para v1: {ok_link}")

        historico = manager.obter_historico_documento(doc_v2.id)
        print(f"   ✅ Histórico: {len(historico)} versões")

        return ok_link and len(historico) >= 1
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    finally:
        safe_delete(doc_v2)
        safe_delete(doc_v1)


def main():
    print("🧪 INICIANDO TESTES COMPLETOS (OFFLINE)")
    print("=" * 70)

    testes = [
        test_setup,
        test_embeddings,
        test_manager,
        test_retrieval,
        test_rag_complete,
        test_versioning,
    ]

    resultados = []
    for teste in testes:
        try:
            resultados.append(bool(teste()))
        except Exception as e:
            print(f"   ❌ Erro crítico: {e}")
            resultados.append(False)

    print("\n" + "=" * 70)
    print("📊 RESULTADOS")
    print("=" * 70)

    total = len(resultados)
    sucesso = sum(resultados)
    falha = total - sucesso

    print(f"✅ Sucesso: {sucesso}/{total}")
    print(f"❌ Falha: {falha}/{total}")

    if falha == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return 0

    print("\n⚠️  ALGUNS TESTES FALHARAM")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
