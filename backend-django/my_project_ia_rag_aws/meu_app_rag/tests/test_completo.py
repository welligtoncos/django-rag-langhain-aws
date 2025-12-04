 
import os
import sys
from pathlib import Path
import time
import django
import argparse


# aponta para .../my_project_ia_rag_aws (onde está o manage.py)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)) 
os.chdir(ROOT)



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project_ia_rag_aws.settings")
django.setup()

# imports do seu projeto SÓ depois do setup
from django.conf import settings
from meu_app_rag.models import Documento, KnowledgeBase
from meu_app_rag.rag.augmenter import ContextAugmenter
from meu_app_rag.rag.embeddings import Embeddings
from meu_app_rag.rag.generator import ResponseGenerator
from meu_app_rag.rag.manager import KnowledgeManager
from meu_app_rag.rag.retriever import MultiBaseRetriever


 

# Imports após Django setup
from django.conf import settings
 


class Colors:
    """Cores para terminal"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestRunner:
    """Executor de testes"""
    
    def __init__(self, pular_claude=False):
        self.testes_passou = 0
        self.testes_falhou = 0
        self.testes_pulados = 0
        self.pular_claude = pular_claude
        self.doc_teste_id = None
        
    def print_header(self, texto):
        """Imprime cabeçalho"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{texto}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.ENDC}\n")
    
    def print_test(self, numero, nome):
        """Imprime nome do teste"""
        print(f"\n{Colors.BOLD}{numero} TESTE: {nome}{Colors.ENDC}")
        print(f"{Colors.BLUE}{'─' * 70}{Colors.ENDC}")
    
    def print_success(self, mensagem):
        """Imprime sucesso"""
        print(f"{Colors.GREEN}   ✅ {mensagem}{Colors.ENDC}")
    
    def print_error(self, mensagem):
        """Imprime erro"""
        print(f"{Colors.RED}   ❌ ERRO: {mensagem}{Colors.ENDC}")
    
    def print_warning(self, mensagem):
        """Imprime aviso"""
        print(f"{Colors.YELLOW}   ⚠️  {mensagem}{Colors.ENDC}")
    
    def print_info(self, mensagem):
        """Imprime informação"""
        print(f"{Colors.CYAN}   ℹ️  {mensagem}{Colors.ENDC}")
    
    def run_test(self, func):
        """Executa um teste e registra resultado"""
        try:
            func()
            self.testes_passou += 1
            return True
        except AssertionError as e:
            self.print_error(f"Asserção falhou: {e}")
            self.testes_falhou += 1
            return False
        except Exception as e:
            self.print_error(f"{type(e).__name__}: {e}")
            self.testes_falhou += 1
            return False
    
    # ==================== TESTES ====================
    
    def test_01_verificacao_inicial(self):
        """Teste 1: Verificação Inicial"""
        self.print_test("1️⃣", "Verificação Inicial")
        
        # Verificar estrutura de arquivos
        self.print_info("Verificando estrutura de arquivos...")
        
        arquivos_necessarios = [
            'manage.py',
            'requirements.txt',
            '.env',
            'my_project_ia_rag_aws/settings.py',
            'meu_app_rag/models.py',
            'meu_app_rag/views.py',
            'meu_app_rag/rag/embeddings.py',
            'meu_app_rag/rag/manager.py',
            'meu_app_rag/rag/retriever.py',
        ]
        
        for arquivo in arquivos_necessarios:
            path = ROOT / arquivo 
            if path.exists():
                self.print_success(f"Arquivo encontrado: {arquivo}")
            else:
                raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
        
        # Verificar variáveis de ambiente
        self.print_info("Verificando variáveis de ambiente...")
        
        variaveis = [
            'SECRET_KEY',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_REGION',
        ]
        
        for var in variaveis:
            valor = getattr(settings, var, None)
            if valor:
                self.print_success(f"{var} configurada")
            else:
                raise ValueError(f"{var} não configurada no .env")
        
        self.print_success("Verificação inicial OK!")
    
    def test_02_database(self):
        """Teste 2: Database"""
        self.print_test("2️⃣", "Database")
        
        # Contar bases
        self.print_info("Verificando bases de conhecimento...")
        bases_count = KnowledgeBase.objects.count()
        
        if bases_count == 0:
            self.print_warning("Nenhuma base encontrada!")
            self.print_info("Execute: python manage.py criar_bases")
            raise AssertionError("Nenhuma base de conhecimento encontrada")
        
        self.print_success(f"Bases encontradas: {bases_count}")
        
        # Listar bases
        bases = KnowledgeBase.objects.all()
        for base in bases:
            docs_count = base.documentos.count()
            self.print_info(f"{base.icone} {base.nome}: {docs_count} documentos")
        
        # Contar documentos
        docs_count = Documento.objects.count()
        docs_ativos = Documento.objects.filter(status='ativo').count()
        
        self.print_success(f"Total de documentos: {docs_count}")
        self.print_success(f"Documentos ativos: {docs_ativos}")
        
        self.print_success("Database OK!")
    
    def test_03_embeddings(self):
        """Teste 3: AWS Bedrock - Embeddings"""
        self.print_test("3️⃣", "AWS Bedrock - Embeddings")
        
        self.print_info("Conectando ao AWS Bedrock...")
        embeddings = Embeddings()
        self.print_success("Conexão estabelecida")
        
        self.print_info("Gerando embedding de teste...")
        texto = "Como faço para batizar meu filho na paróquia?"
        
        inicio = time.time()
        vetor = embeddings.embed(texto)
        tempo = time.time() - inicio
        
        self.print_success(f"Embedding gerado em {tempo:.2f}s")
        self.print_info(f"Dimensões: {len(vetor)}")
        self.print_info(f"Tipo: {type(vetor).__name__}")
        self.print_info(f"Primeiros 5 valores: {vetor[:5].tolist()}")
        
        # Verificações
        assert len(vetor) == 1024, f"Embedding deve ter 1024 dimensões, tem {len(vetor)}"
        import numpy as np # pyright: ignore[reportMissingImports]
        assert np.issubdtype(vetor.dtype, np.number), "Valores devem ser numéricos"
        
        self.print_success("Embeddings OK!")
    
    def test_04_knowledge_manager(self):
        """Teste 4: Knowledge Manager"""
        self.print_test("4️⃣", "Knowledge Manager")
        
        manager = KnowledgeManager()
        self.print_success("Manager criado")
        
        # Buscar base
        self.print_info("Buscando base de conhecimento...")
        base = KnowledgeBase.objects.first()
        
        if not base:
            raise AssertionError("Nenhuma base encontrada. Execute: python manage.py criar_bases")
        
        self.print_success(f"Base encontrada: {base.nome}")
        
        # Adicionar documento de teste
        self.print_info("Adicionando documento de teste...")
        
        doc = manager.adicionar_documento(
            base=base,
            titulo="TESTE AUTOMATIZADO - Batismo",
            conteudo="""
# BATISMO - DOCUMENTO DE TESTE AUTOMATIZADO

## Documentos Necessários
- Certidão de nascimento da criança (original e cópia)
- RG e CPF dos pais
- Comprovante de residência atualizado
- Certidão de casamento religioso dos pais (se casados na igreja)
- Declaração de padrinho/madrinha (emitida pela paróquia de origem)

## Como Agendar
- Telefone: (11) 1234-5678
- WhatsApp: (11) 98765-4321
- Antecedência mínima: 45 dias antes da data desejada
- Ideal: 2 a 3 meses de antecedência

## Curso de Preparação
- Obrigatório para pais e padrinhos
- Duração: 2 encontros aos sábados
- Horário: 14h às 17h
- Inscrição: presencial na secretaria
- Custo: gratuito

## Datas Disponíveis
- Aos domingos: após a missa das 10h (11h30)
- Quantidade máxima: 6 crianças por celebração
- Agendamento: após conclusão do curso

## Valores e Taxas
- Não há taxa obrigatória para o sacramento
- Ofertas voluntárias são aceitas
- Flores para decoração: por conta da família (opcional)

## Importante
- Padrinho/madrinha deve ter mais de 16 anos
- Deve ter recebido o sacramento da Crisma
- Pelo menos um dos padrinhos deve ser católico praticante
- Máximo de 2 padrinhos (pode ser apenas 1)

## Mais Informações
- Secretaria: Segunda a sexta, 9h às 17h
- E-mail: secretaria@paroquia.com
            """,
            categoria="Sacramentos",
            tags=["batismo", "teste", "automatizado", "documentos"],
            gerar_embedding=True
        )
        
        self.doc_teste_id = doc.id  # Salvar para limpeza posterior
        
        self.print_success(f"Documento criado! ID: {doc.id}")
        self.print_info(f"Título: {doc.titulo}")
        self.print_info(f"Versão: {doc.versao}")
        self.print_info(f"Status: {doc.status}")
        self.print_info(f"Embedding gerado: {'Sim' if doc.embedding else 'Não'}")
        
        if doc.embedding:
            self.print_info(f"Dimensões do embedding: {len(doc.embedding)}")
        
        # Verificações
        assert doc.id is not None, "Documento deve ter ID"
        assert doc.embedding is not None, "Documento deve ter embedding"
        assert len(doc.embedding) == 1024, "Embedding deve ter 1024 dimensões"
        assert doc.status == 'ativo', "Documento deve estar ativo"
        
        self.print_success("Knowledge Manager OK!")
    
    def test_05_retriever(self):
        """Teste 5: Retriever - Busca Vetorial"""
        self.print_test("5️⃣", "Retriever - Busca Vetorial")
        
        retriever = MultiBaseRetriever()
        self.print_success("Retriever criado")
        
        # Fazer busca
        query = "quais documentos preciso para batizar meu filho"
        self.print_info(f"Query: '{query}'")
        
        inicio = time.time()
        resultados = retriever.retrieve(
            query=query,
            limit=5
        )
        tempo = time.time() - inicio
        
        self.print_success(f"Busca realizada em {tempo:.2f}s")
        self.print_info(f"Documentos encontrados: {len(resultados)}")
        
        if len(resultados) == 0:
            raise AssertionError("Nenhum documento encontrado (esperado pelo menos 1)")
        
        # Mostrar resultados
        print(f"\n{Colors.CYAN}   📊 Resultados da busca:{Colors.ENDC}")
        for i, doc in enumerate(resultados, 1):
            print(f"{Colors.CYAN}   {i}. {doc['titulo']}{Colors.ENDC}")
            print(f"{Colors.CYAN}      Base: {doc['base']['nome']} {doc['base']['icone']}{Colors.ENDC}")
            print(f"{Colors.CYAN}      Score: {doc['score']:.4f}{Colors.ENDC}")
        
        # Verificações
        melhor = resultados[0]
        assert melhor['score'] > 0.3, f"Score muito baixo: {melhor['score']}"
        
        # Verificar se encontrou documento sobre batismo
        encontrou_batismo = any(
            'batismo' in doc['titulo'].lower() or 
            'batismo' in doc.get('categoria', '').lower() or
            'batismo' in str(doc.get('tags', [])).lower()
            for doc in resultados
        )
        
        if encontrou_batismo:
            self.print_success("Documento sobre batismo encontrado!")
        else:
            self.print_warning("Documento sobre batismo não está no top-5")
        
        self.print_success("Retriever OK!")
        
        return resultados  # Retorna para próximos testes
    
    def test_06_augmenter(self, resultados):
        """Teste 6: Augmenter - Formatação de Contexto"""
        self.print_test("6️⃣", "Augmenter - Formatação de Contexto")
        
        augmenter = ContextAugmenter()
        self.print_success("Augmenter criado")
        
        query = "quais documentos preciso para batizar"
        self.print_info(f"Query: '{query}'")
        
        inicio = time.time()
        contexto = augmenter.augment(query, resultados)
        tempo = time.time() - inicio
        
        self.print_success(f"Contexto gerado em {tempo:.2f}s")
        self.print_info(f"Tamanho: {len(contexto)} caracteres")
        
        # Mostrar preview
        print(f"\n{Colors.CYAN}   📄 Preview do contexto (primeiros 300 chars):{Colors.ENDC}")
        print(f"{Colors.CYAN}   {'─' * 66}{Colors.ENDC}")
        preview = contexto[:300].replace('\n', '\n   ')
        print(f"{Colors.CYAN}   {preview}...{Colors.ENDC}")
        print(f"{Colors.CYAN}   {'─' * 66}{Colors.ENDC}")
        
        # Verificações
        assert len(contexto) > 100, "Contexto muito curto"
        assert "CONSULTA DO USUÁRIO" in contexto, "Contexto deve conter a query"
        assert "INSTRUÇÕES" in contexto or "instruções" in contexto.lower(), \
               "Contexto deve conter instruções"
        
        # Verificar se tem documentos
        assert len(resultados) > 0, "Deve ter pelo menos 1 documento no contexto"
        
        self.print_success("Augmenter OK!")
        
        return contexto  # Retorna para próximo teste
    
    def test_07_generator(self, contexto, query):
        """Teste 7: Generator - Claude Bedrock"""
        self.print_test("7️⃣", "Generator - Claude Bedrock")
        
        if self.pular_claude:
            self.print_warning("Teste pulado (--sem-claude)")
            self.testes_pulados += 1
            return
        
        self.print_warning("Este teste usa Claude (custo ~$0.003)")
        
        generator = ResponseGenerator()
        self.print_success("Generator criado")
        
        self.print_info(f"Query: '{query}'")
        self.print_info("Gerando resposta com Claude...")
        
        inicio = time.time()
        resposta = generator.generate(contexto, query)
        tempo = time.time() - inicio
        
        self.print_success(f"Resposta gerada em {tempo:.2f}s")
        self.print_info(f"Tamanho da resposta: {len(resposta)} caracteres")
        
        # Mostrar resposta
        print(f"\n{Colors.CYAN}   💬 Resposta do Claude:{Colors.ENDC}")
        print(f"{Colors.CYAN}   {'─' * 66}{Colors.ENDC}")
        resposta_formatada = resposta[:500].replace('\n', '\n   ')
        print(f"{Colors.CYAN}   {resposta_formatada}...{Colors.ENDC}")
        print(f"{Colors.CYAN}   {'─' * 66}{Colors.ENDC}")
        
        # Verificações
        assert len(resposta) > 50, "Resposta muito curta"
        
        # Verificar se resposta menciona documentos
        palavras_chave = ['certidão', 'documento', 'rg', 'cpf', 'comprovante']
        menciona_docs = any(palavra in resposta.lower() for palavra in palavras_chave)
        
        if menciona_docs:
            self.print_success("Resposta menciona documentos relevantes")
        else:
            self.print_warning("Resposta não menciona documentos esperados")
        
        self.print_success("Generator OK!")
    
    def test_08_versionamento(self):
        """Teste 8: Versionamento"""
        self.print_test("8️⃣", "Versionamento de Documentos")
        
        if not self.doc_teste_id:
            self.print_warning("Nenhum documento de teste disponível")
            self.testes_pulados += 1
            return
        
        manager = KnowledgeManager()
        
        # Buscar documento
        doc_v1 = Documento.objects.get(id=self.doc_teste_id)
        self.print_info(f"Documento original: {doc_v1.titulo} (v{doc_v1.versao})")
        
        # Atualizar (cria v2)
        self.print_info("Atualizando documento (cria v2)...")
        
        doc_v2 = manager.atualizar_documento(
            documento_id=doc_v1.id,
            titulo=f"{doc_v1.titulo} - ATUALIZADO",
            conteudo=doc_v1.conteudo + "\n\n## ATUALIZAÇÃO\n\nNovas informações adicionadas pelo teste automatizado."
        )
        
        self.print_success(f"Nova versão criada: v{doc_v2.versao}")
        self.print_info(f"Documento anterior: ID {doc_v2.documento_anterior.id}")
        
        # Verificar v1 foi arquivada
        doc_v1.refresh_from_db()
        assert doc_v1.status == 'arquivado', "v1 deve estar arquivada"
        self.print_success("v1 arquivada corretamente")
        
        # Ver histórico
        self.print_info("Consultando histórico...")
        historico = manager.obter_historico_documento(doc_v2.id)
        
        self.print_success(f"Histórico: {len(historico)} versões")
        for v in historico:
            status_emoji = "✓" if v.status == "ativo" else "📦"
            self.print_info(f"{status_emoji} v{v.versao}: {v.status}")
        
        assert len(historico) == 2, "Deve ter 2 versões"
        
        # Restaurar v1
        self.print_info("Restaurando v1...")
        doc_v3 = manager.restaurar_versao(doc_v2.id, 1)
        
        self.print_success(f"v1 restaurada como v{doc_v3.versao}")
        
        # Verificar
        assert doc_v3.versao == 3, "Deve ser v3"
        assert doc_v3.titulo == doc_v1.titulo, "Título deve ser da v1"
        
        self.print_success("Versionamento OK!")
    
    def test_09_expiracao(self):
        """Teste 9: Expiração de Documentos"""
        self.print_test("9️⃣", "Expiração de Documentos")
        
        from datetime import timedelta
        from django.utils import timezone
        
        manager = KnowledgeManager()
        
        # Buscar base temporária
        base_avisos = KnowledgeBase.objects.filter(slug='avisos-semanais').first()
        
        if not base_avisos:
            self.print_warning("Base 'avisos-semanais' não encontrada")
            self.testes_pulados += 1
            return
        
        # Criar documento com expiração
        self.print_info("Criando documento temporário...")
        
        hoje = timezone.now()
        doc_temp = manager.adicionar_documento(
            base=base_avisos,
            titulo="TESTE - Documento Temporário",
            conteudo="Este documento expira em 7 dias (teste automatizado)",
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=7),
            gerar_embedding=False  # Não precisa para teste de expiração
        )
        
        self.print_success(f"Documento criado: ID {doc_temp.id}")
        self.print_info(f"Expira em: {doc_temp.data_fim.strftime('%d/%m/%Y')}")
        self.print_info(f"Válido: {doc_temp.is_valido()}")
        
        assert doc_temp.is_valido(), "Documento deve estar válido"
        
        # Forçar expiração
        self.print_info("Forçando expiração (alterando data)...")
        doc_temp.data_fim = hoje - timedelta(days=1)
        doc_temp.save()
        
        self.print_info(f"Nova data fim: {doc_temp.data_fim.strftime('%d/%m/%Y')}")
        self.print_info(f"Válido: {doc_temp.is_valido()}")
        
        assert not doc_temp.is_valido(), "Documento deve estar inválido"
        
        # Executar expiração
        self.print_info("Executando comando de expiração...")
        total_expirado = manager.expirar_documentos_vencidos()
        
        self.print_success(f"Documentos expirados: {total_expirado}")
        
        # Verificar status
        doc_temp.refresh_from_db()
        self.print_info(f"Status final: {doc_temp.status}")
        
        assert doc_temp.status == 'expirado', "Documento deve estar expirado"
        
        # Limpar
        doc_temp.delete()
        
        self.print_success("Expiração OK!")
    
    def test_10_estatisticas(self):
        """Teste 10: Estatísticas do Sistema"""
        self.print_test("🔟", "Estatísticas do Sistema")
        
        manager = KnowledgeManager()
        
        self.print_info("Coletando estatísticas...")
        stats = manager.obter_estatisticas()
        
        self.print_success("Estatísticas coletadas!")
        
        print(f"\n{Colors.CYAN}   📊 Estatísticas:{Colors.ENDC}")
        print(f"{Colors.CYAN}   {'─' * 66}{Colors.ENDC}")
        print(f"{Colors.CYAN}   Total de bases: {stats['total_bases']}{Colors.ENDC}")
        print(f"{Colors.CYAN}   Bases ativas: {stats['bases_ativas']}{Colors.ENDC}")
        print(f"{Colors.CYAN}   Total de documentos: {stats['total_documentos']}{Colors.ENDC}")
        
        print(f"\n{Colors.CYAN}   📈 Por status:{Colors.ENDC}")
        for status, count in stats['documentos_por_status'].items():
            print(f"{Colors.CYAN}      {status}: {count}{Colors.ENDC}")
        
        print(f"\n{Colors.CYAN}   📚 Por base:{Colors.ENDC}")
        for base, count in stats['documentos_por_base'].items():
            print(f"{Colors.CYAN}      {base}: {count}{Colors.ENDC}")
        
        print(f"{Colors.CYAN}   {'─' * 66}{Colors.ENDC}")
        
        # Verificações básicas
        assert stats['total_bases'] > 0, "Deve ter pelo menos 1 base"
        assert stats['total_documentos'] >= 0, "Total de documentos deve ser >= 0"
        
        self.print_success("Estatísticas OK!")
    
    def cleanup(self):
        """Limpar documentos de teste"""
        self.print_info("\n🧹 Limpando documentos de teste...")
        
        # Deletar documentos de teste
        docs_teste = Documento.objects.filter(
            titulo__icontains="TESTE"
        )
        
        count = docs_teste.count()
        if count > 0:
            docs_teste.delete()
            self.print_success(f"{count} documento(s) de teste removido(s)")
        else:
            self.print_info("Nenhum documento de teste para remover")
    
    def print_summary(self):
        """Imprime resumo final"""
        self.print_header("📊 RESUMO FINAL")
        
        total = self.testes_passou + self.testes_falhou
        percentual = (self.testes_passou / total * 100) if total > 0 else 0
        
        print(f"{Colors.BOLD}Total de testes: {total}{Colors.ENDC}")
        print(f"{Colors.GREEN}✅ Passou: {self.testes_passou}/{total} ({percentual:.1f}%){Colors.ENDC}")
        
        if self.testes_falhou > 0:
            print(f"{Colors.RED}❌ Falhou: {self.testes_falhou}/{total}{Colors.ENDC}")
        
        if self.testes_pulados > 0:
            print(f"{Colors.YELLOW}⏭️  Pulados: {self.testes_pulados}{Colors.ENDC}")
        
        print()
        
        if self.testes_falhou == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}🎉 TODOS OS TESTES PASSARAM!{Colors.ENDC}")
            return 0
        else:
            print(f"{Colors.RED}{Colors.BOLD}⚠️  ALGUNS TESTES FALHARAM{Colors.ENDC}")
            return 1
    
    def run_all(self):
        """Executa todos os testes"""
        self.print_header("🧪 TESTE COMPLETO DO SISTEMA RAG - PARÓQUIA")
        
        print(f"{Colors.CYAN}Iniciando bateria de testes...{Colors.ENDC}")
        print(f"{Colors.CYAN}Data/Hora: {time.strftime('%d/%m/%Y %H:%M:%S')}{Colors.ENDC}\n")
        
        inicio_geral = time.time()
        
        try:
            # Fase 1: Verificação Inicial
            self.run_test(self.test_01_verificacao_inicial)
            
            # Fase 2: Database
            self.run_test(self.test_02_database)
            
            # Fase 3: Embeddings
            self.run_test(self.test_03_embeddings)
            
            # Fase 4: Knowledge Manager
            self.run_test(self.test_04_knowledge_manager)
            
            # Fase 5: Retriever
            resultados = []
            if self.run_test(lambda: None):  # Placeholder
                try:
                    resultados = self.test_05_retriever()
                    self.testes_passou += 1
                except Exception as e:
                    self.print_error(str(e))
                    self.testes_falhou += 1
            
            # Fase 6: Augmenter
            contexto = ""
            if resultados:
                if self.run_test(lambda: None):  # Placeholder
                    try:
                        contexto = self.test_06_augmenter(resultados)
                        self.testes_passou += 1
                    except Exception as e:
                        self.print_error(str(e))
                        self.testes_falhou += 1
            
            # Fase 7: Generator (Claude)
            if contexto:
                if self.run_test(lambda: None):  # Placeholder
                    try:
                        query = "quais documentos preciso para batizar"
                        self.test_07_generator(contexto, query)
                        if not self.pular_claude:
                            self.testes_passou += 1
                    except Exception as e:
                        if not self.pular_claude:
                            self.print_error(str(e))
                            self.testes_falhou += 1
            
            # Fase 8: Versionamento
            self.run_test(self.test_08_versionamento)
            
            # Fase 9: Expiração
            self.run_test(self.test_09_expiracao)
            
            # Fase 10: Estatísticas
            self.run_test(self.test_10_estatisticas)
            
        finally:
            # Sempre limpar
            self.cleanup()
        
        tempo_total = time.time() - inicio_geral
        
        print(f"\n{Colors.CYAN}⏱️  Tempo total: {tempo_total:.2f}s{Colors.ENDC}")
        
        return self.print_summary()


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Script de Teste Completo do Sistema RAG'
    )
    parser.add_argument(
        '--sem-claude',
        action='store_true',
        help='Pula teste do Claude (economizar custo API)'
    )
    
    args = parser.parse_args()
    
    runner = TestRunner(pular_claude=args.sem_claude)
    return runner.run_all()


if __name__ == '__main__':
    sys.exit(main())