import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_project_ia_rag_aws.settings')
django.setup()

from meu_app_rag.models import KnowledgeBase, Documento
from meu_app_rag.rag.manager import KnowledgeManager
from meu_app_rag.rag.retriever import MultiBaseRetriever

def print_step(step, msg):
    print(f"\n🔹 [PASSO {step}] {msg}")

def print_success(msg):
    print(f"   ✅ {msg}")

def print_error(msg):
    print(f"   ❌ {msg}")

def validate_parish_context():
    print("🚀 INICIANDO VALIDAÇÃO AVANÇADA (CONTEXTO PAROQUIAL)")
    print("====================================================")
    
    manager = KnowledgeManager()
    slug_base = "secretaria-teste"
    
    # 1. Criar Base
    print_step(1, "Criando Base 'Secretaria'")
    base, _ = KnowledgeBase.objects.get_or_create(
        slug=slug_base,
        defaults={
            'nome': "Secretaria (Teste)",
            'tipo': "temporario",
            'descricao': "Regras e sacramentos",
            'icone': "⛪",
            'auto_expiracao': True,
            'dias_expiracao': 1
        }
    )
    print_success("Base pronta.")

    # 2. Criar Documentos (Target + Distratores)
    print_step(2, "Inserindo Documentos Complexos")
    
    docs_data = [
        {
            "titulo": "Regras para Batismo de Crianças (0 a 7 anos)",
            "conteudo": """
            Para batizar crianças menores de 7 anos, os pais devem ser casados na Igreja ou estarem em preparação.
            REGRAS PARA PADRINHOS:
            1. Devem ser católicos, maiores de 16 anos.
            2. Devem ter recebido o sacramento da Crisma.
            3. Se forem casados, devem ser casados na Igreja Católica.
            4. Pessoas em união estável ou solteiros que vivem juntos não podem ser padrinhos.
            """,
            "tags": ["batismo", "crianca", "regras", "padrinhos"]
        },
        {
            "titulo": "Batismo de Adultos (Catecumenato)",
            "conteudo": """
            Adultos não batizados devem passar pelo processo de RICA (Rito de Iniciação Cristã de Adultos).
            O processo dura cerca de 1 ano.
            Não há necessidade de padrinhos no mesmo sentido do batismo infantil, mas sim de um introdutor.
            """,
            "tags": ["batismo", "adulto", "rica"]
        },
        {
            "titulo": "Curso de Noivos e Casamento",
            "conteudo": """
            Para casar na Igreja, é necessário fazer o curso de noivos.
            Os padrinhos de casamento não precisam ser católicos, mas devem ser testemunhas idôneas.
            """,
            "tags": ["casamento", "noivos", "matrimonio"]
        }
    ]
    
    # Limpa anteriores
    Documento.objects.filter(base=base).delete()
    
    target_doc_id = None
    
    for d in docs_data:
        doc = manager.adicionar_documento(
            base=base,
            titulo=d['titulo'],
            conteudo=d['conteudo'],
            categoria="Sacramentos",
            tags=d['tags'],
            gerar_embedding=True
        )
        if "Crianças" in d['titulo']:
            target_doc_id = doc.id
            
    print_success(f"{len(docs_data)} documentos inseridos e vetorizados.")

    # 3. Teste Difícil (Semantic Search)
    print_step(3, "Teste de Busca Semântica (Difícil)")
    
    # A pergunta NÃO usa as palavras "regras", "padrinhos" ou "crisma".
    # Ela descreve uma SITUAÇÃO que exige o documento de regras de batismo infantil.
    query = "Meus compadres moram juntos mas não casaram no papel, eles podem levar meu filho na pia batismal?"
    
    print(f"   ❓ Pergunta do fiel: '{query}'")
    print("   (Esperamos que o sistema entenda que 'levar na pia batismal' = ser padrinho e encontre as regras)")
    
    retriever = MultiBaseRetriever()
    resultados = retriever.retrieve(query=query, bases=[slug_base], limit=3)
    
    encontrou_alvo = False
    posicao = -1
    
    print("\n   🔎 Resultados encontrados:")
    for i, res in enumerate(resultados):
        is_target = (res['id'] == target_doc_id)
        marcador = "✅ ALVO" if is_target else "❌"
        print(f"      {i+1}. [{res['score']:.4f}] {res['titulo']} {marcador}")
        
        if is_target:
            encontrou_alvo = True
            posicao = i + 1

    print("\n   CONCLUSÃO:")
    if encontrou_alvo:
        if posicao == 1:
            print_success("SUCESSO TOTAL! O documento correto foi o primeiro resultado.")
            print("      A IA entendeu que 'morar junto' e 'levar na pia' tem a ver com as regras de padrinhos.")
        else:
            print(f"   ⚠️  Atenção: O documento correto apareceu na posição {posicao}, mas não foi o primeiro.")
    else:
        print_error("FALHA: O documento com as regras não foi encontrado nos top 3.")

if __name__ == "__main__":
    validate_parish_context()
