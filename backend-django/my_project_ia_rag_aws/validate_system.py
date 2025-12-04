import os
import django
import time
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
    sys.exit(1)

def validate_system():
    print("🚀 INICIANDO VALIDAÇÃO DO SISTEMA RAG")
    print("=====================================")
    
    manager = KnowledgeManager()
    slug_base = "validacao-sistema"
    
    # 1. Criar Base
    print_step(1, "Criando Base de Conhecimento de Teste")
    try:
        base, created = KnowledgeBase.objects.get_or_create(
            slug=slug_base,
            defaults={
                'nome': "Validação do Sistema",
                'tipo': "temporario",
                'descricao': "Base usada para validar o funcionamento do RAG",
                'icone': "🧪",
                'auto_expiracao': True,
                'dias_expiracao': 1
            }
        )
        if created:
            print_success(f"Base criada: {base.nome}")
        else:
            print_success(f"Base já existia: {base.nome}")
            
    except Exception as e:
        print_error(f"Erro ao criar base: {e}")

    # 2. Criar Documento
    print_step(2, "Criando Documento de Teste")
    titulo_doc = "Protocolo de Teste Omega"
    conteudo_doc = """
    O Protocolo de Teste Omega é um procedimento de segurança padrão.
    Ele deve ser ativado quando a temperatura do servidor exceder 85 graus Celsius.
    A primeira etapa é notificar o administrador via SMS.
    A segunda etapa é desligar os clusters não essenciais.
    A senha de emergência é 'DELTA-99'.
    """
    
    try:
        # Remove se já existir para testar do zero
        Documento.objects.filter(base=base, titulo=titulo_doc).delete()
        
        doc = manager.adicionar_documento(
            base=base,
            titulo=titulo_doc,
            conteudo=conteudo_doc,
            categoria="Protocolos",
            tags=["teste", "seguranca", "omega"],
            gerar_embedding=True
        )
        print_success(f"Documento criado: {doc.titulo} (ID: {doc.id})")
        
    except Exception as e:
        print_error(f"Erro ao criar documento: {e}")

    # 3. Verificar Embedding
    print_step(3, "Verificando Geração de Embedding")
    
    # Recarrega do banco
    doc.refresh_from_db()
    
    if doc.embedding:
        print_success(f"Embedding gerado com sucesso! ({len(doc.embedding)} dimensões)")
    else:
        print_error("Embedding NÃO foi gerado. Verifique as credenciais da AWS ou logs de erro.")

    # 4. Testar Recuperação (Retrieval)
    print_step(4, "Testando Busca (Retrieval)")
    
    retriever = MultiBaseRetriever()
    query = "qual a senha de emergência do protocolo omega?"
    
    print(f"   🔎 Buscando por: '{query}'")
    
    try:
        resultados = retriever.retrieve(
            query=query,
            bases=[slug_base],
            limit=3
        )
        
        encontrou = False
        for res in resultados:
            print(f"      - Encontrado: {res['titulo']} (Score: {res['score']:.4f})")
            if res['id'] == doc.id:
                encontrou = True
        
        if encontrou:
            print_success("Documento correto encontrado na busca!")
        else:
            print_error("O documento criado NÃO apareceu nos resultados da busca.")
            
    except Exception as e:
        print_error(f"Erro na busca: {e}")

    # 5. Limpeza (Opcional)
    print_step(5, "Limpeza")
    # manager.desativar_base(slug_base)
    print_success("Teste finalizado. A base de teste foi mantida para inspeção.")
    
    print("\n🎉 VALIDAÇÃO CONCLUÍDA COM SUCESSO! O SISTEMA ESTÁ OPERACIONAL.")

if __name__ == "__main__":
    validate_system()
