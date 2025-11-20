# test_rag_stress.py
import os
import sys
import time
import json
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import statistics

# Configurações
API_BASE_URL = "http://localhost:8000/api"
MAX_WORKERS = 10  # Threads para testes de concorrência

# ============================================
# 🎯 CASOS DE TESTE - CATEGORIAS
# ============================================

class TesteSuites:
    """Suítes de testes organizadas por categoria"""
    
    # ========================================
    # 1. CONSULTAS SIMPLES
    # ========================================
    CONSULTAS_SIMPLES = [
        "camiseta",
        "calça",
        "tênis",
        "roupa",
        "eletrônico",
        "perfume",
        "mochila",
        "fone",
        "moletom",
        "cadeira"
    ]
    
    # ========================================
    # 2. CONSULTAS COM CARACTERÍSTICAS
    # ========================================
    CONSULTAS_CARACTERISTICAS = [
        "camiseta branca",
        "tênis de corrida",
        "calça jeans azul",
        "mochila para notebook",
        "perfume masculino",
        "fone bluetooth",
        "smartwatch com GPS",
        "moletom cinza",
        "cadeira gamer",
        "vestido floral"
    ]
    
    # ========================================
    # 3. CONSULTAS POR PREÇO
    # ========================================
    CONSULTAS_PRECO = [
        "produtos baratos",
        "produtos até 100 reais",
        "produtos entre 100 e 200 reais",
        "produtos acima de 500 reais",
        "produto mais barato",
        "produto mais caro",
        "melhor custo benefício",
        "promoções",
        "produtos em promoção",
        "descontos"
    ]
    
    # ========================================
    # 4. CONSULTAS POR CATEGORIA
    # ========================================
    CONSULTAS_CATEGORIA = [
        "roupas masculinas",
        "roupas femininas",
        "eletrônicos",
        "calçados",
        "acessórios",
        "produtos de beleza",
        "móveis",
        "tecnologia",
        "moda",
        "fitness"
    ]
    
    # ========================================
    # 5. CONSULTAS COMPLEXAS
    # ========================================
    CONSULTAS_COMPLEXAS = [
        "quero uma camiseta branca de algodão com boa avaliação",
        "preciso de um tênis confortável para corrida até 200 reais",
        "estou procurando uma mochila para trabalho com compartimento para notebook",
        "qual o melhor smartwatch com GPS e monitor cardíaco?",
        "quero um perfume masculino sofisticado e duradouro",
        "procuro uma cadeira ergonômica para home office em promoção",
        "preciso de um fone bluetooth com cancelamento de ruído",
        "qual vestido floral você recomenda para casamento?",
        "quero montar um look completo com calça jeans e camiseta",
        "qual produto tem melhor avaliação na categoria eletrônicos?"
    ]
    
    # ========================================
    # 6. CONSULTAS DE COMPARAÇÃO
    # ========================================
    CONSULTAS_COMPARACAO = [
        "compare tênis de corrida",
        "qual a diferença entre os smartwatches?",
        "moletom ou camiseta?",
        "qual melhor: fone bluetooth ou com fio?",
        "compare os perfumes masculinos",
        "qual cadeira tem melhor custo-benefício?",
        "produtos similares à camiseta básica",
        "alternativas ao tênis pro run",
        "compare preços de eletrônicos",
        "qual tem melhor avaliação?"
    ]
    
    # ========================================
    # 7. CONSULTAS DE DISPONIBILIDADE
    # ========================================
    CONSULTAS_DISPONIBILIDADE = [
        "produtos em estoque",
        "produtos disponíveis imediatamente",
        "tem camiseta branca disponível?",
        "qual o estoque do tênis?",
        "produtos com estoque baixo",
        "produtos esgotados",
        "quando chega mais estoque?",
        "produtos para entrega rápida",
        "disponibilidade de eletrônicos",
        "tem em estoque?"
    ]
    
    # ========================================
    # 8. CONSULTAS POR MARCA
    # ========================================
    CONSULTAS_MARCA = [
        "produtos da marca BasicWear",
        "tênis SportPro",
        "qual a melhor marca de eletrônicos?",
        "produtos TechFit",
        "marcas disponíveis de perfume",
        "produtos GameSeats",
        "marcas de roupa",
        "qual marca tem melhor avaliação?",
        "produtos ComfortWear",
        "marcas premium"
    ]
    
    # ========================================
    # 9. CONSULTAS DE RECOMENDAÇÃO
    # ========================================
    CONSULTAS_RECOMENDACAO = [
        "me recomende um produto",
        "o que você sugere?",
        "qual o melhor produto?",
        "recomende algo para presente",
        "produto mais vendido",
        "produto mais popular",
        "melhor avaliado",
        "produto do momento",
        "tendências",
        "novidades"
    ]
    
    # ========================================
    # 10. CONSULTAS EDGE CASES
    # ========================================
    CONSULTAS_EDGE_CASES = [
        "",  # Vazia
        "   ",  # Apenas espaços
        "a",  # 1 caractere
        "ab",  # 2 caracteres
        "xyz123",  # Sem sentido
        "produto que não existe",
        "sdkfjhsdkjfhskdjfhskjdfh",  # Gibberish
        "!!!???",  # Apenas símbolos
        "🤖🚀💻",  # Apenas emojis
        "produto produto produto produto produto produto",  # Repetição
        "A" * 600,  # Muito longo (> 500 chars)
        "nike adidas puma",  # Marcas que não existem
        "iPhone MacBook AirPods",  # Produtos que não existem
        "quanto custa?",  # Sem especificar produto
        "sim",  # Resposta curta
        "não",  # Negação
        "talvez",  # Indefinido
        "preciso de ajuda",  # Genérico
        "olá",  # Saudação
        "tchau"  # Despedida
    ]
    
    # ========================================
    # 11. CONSULTAS DE ESPECIFICAÇÕES
    # ========================================
    CONSULTAS_ESPECIFICACOES = [
        "camiseta de algodão",
        "calça com elastano",
        "tênis com solado EVA",
        "smartwatch com AMOLED",
        "mochila impermeável",
        "perfume amadeirado",
        "fone com ANC",
        "moletom com capuz",
        "cadeira até 150kg",
        "vestido de viscose"
    ]
    
    # ========================================
    # 12. CONSULTAS CONVERSACIONAIS
    # ========================================
    CONSULTAS_CONVERSACIONAIS = [
        "oi, tudo bem?",
        "você pode me ajudar?",
        "estou procurando um presente",
        "preciso de uma roupa para trabalho",
        "vou correr amanhã, o que preciso?",
        "tenho reunião importante",
        "quero começar home office",
        "preciso renovar guarda-roupa",
        "aniversário do meu namorado",
        "natal chegando"
    ]
    
    # ========================================
    # 13. CONSULTAS DE FILTROS MÚLTIPLOS
    # ========================================
    CONSULTAS_FILTROS_MULTIPLOS = [
        "camiseta branca de algodão até 50 reais em estoque",
        "tênis de corrida preto ou azul com desconto",
        "eletrônicos entre 300 e 600 reais bem avaliados",
        "roupa feminina floral tamanho M em promoção",
        "produtos de beleza masculinos até 300 reais",
        "acessórios práticos para trabalho com entrega rápida",
        "móveis ergonômicos em promoção acima de 4 estrelas",
        "tecnologia bluetooth com cancelamento de ruído",
        "roupas confortáveis tamanho M cinza ou preto",
        "produtos premium bem avaliados em estoque"
    ]
    
    # ========================================
    # 14. CONSULTAS DE ANÁLISE
    # ========================================
    CONSULTAS_ANALISE = [
        "qual produto tem mais avaliações?",
        "qual categoria tem mais produtos?",
        "quantos produtos em promoção?",
        "média de preços",
        "produto mais avaliado",
        "estatísticas do catálogo",
        "quantos produtos em estoque?",
        "faixa de preço dos produtos",
        "marcas disponíveis",
        "resumo do catálogo"
    ]
    
    # ========================================
    # 15. CONSULTAS DE INTENÇÃO VAGA
    # ========================================
    CONSULTAS_VAGAS = [
        "algo legal",
        "produto interessante",
        "qualquer coisa",
        "o que tem?",
        "mostre tudo",
        "produtos novos",
        "surpresa",
        "recomende algo diferente",
        "produto único",
        "algo especial"
    ]

# ============================================
# 🔧 FUNÇÕES DE TESTE
# ============================================

class RAGTester:
    """Classe para executar testes no sistema RAG"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.resultados = []
        self.erros = []
        self.stats = {
            'total': 0,
            'sucesso': 0,
            'erro': 0,
            'tempo_total': 0,
            'tempo_medio': 0,
            'tempo_min': float('inf'),
            'tempo_max': 0,
            'tempos': []
        }
    
    def testar_consulta(self, query: str, limit: int = 5) -> Dict:
        """Testa uma consulta individual"""
        try:
            start = time.time()
            
            response = requests.post(
                f"{self.base_url}/rag/query/",
                json={"query": query, "limit": limit},
                timeout=30
            )
            
            tempo = time.time() - start
            
            resultado = {
                'query': query,
                'status': response.status_code,
                'tempo': round(tempo, 3),
                'sucesso': response.status_code == 200,
                'timestamp': datetime.now().isoformat()
            }
            
            if response.status_code == 200:
                data = response.json()
                resultado['produtos_encontrados'] = data.get('produtos_encontrados', 0)
                resultado['tempo_processamento'] = data.get('tempo_processamento', 0)
                resultado['resposta_length'] = len(data.get('resposta', ''))
                self.stats['sucesso'] += 1
            else:
                resultado['erro'] = response.text
                self.stats['erro'] += 1
                self.erros.append(resultado)
            
            self.stats['total'] += 1
            self.stats['tempo_total'] += tempo
            self.stats['tempos'].append(tempo)
            self.stats['tempo_min'] = min(self.stats['tempo_min'], tempo)
            self.stats['tempo_max'] = max(self.stats['tempo_max'], tempo)
            
            self.resultados.append(resultado)
            return resultado
            
        except Exception as e:
            resultado = {
                'query': query,
                'status': 'EXCEPTION',
                'tempo': 0,
                'sucesso': False,
                'erro': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.stats['erro'] += 1
            self.erros.append(resultado)
            self.resultados.append(resultado)
            return resultado
    
    def testar_suite(self, suite_name: str, consultas: List[str], verbose: bool = True):
        """Testa uma suíte completa de consultas"""
        print(f"\n{'='*80}")
        print(f"🧪 TESTANDO: {suite_name}")
        print(f"{'='*80}")
        print(f"Total de consultas: {len(consultas)}\n")
        
        for i, query in enumerate(consultas, 1):
            if verbose:
                print(f"[{i}/{len(consultas)}] Testando: '{query[:50]}...'", end=' ')
            
            resultado = self.testar_consulta(query)
            
            if verbose:
                if resultado['sucesso']:
                    print(f"✅ {resultado['tempo']}s")
                else:
                    print(f"❌ {resultado.get('erro', 'Erro desconhecido')[:50]}")
        
        print(f"\n{'='*80}\n")
    
    def teste_concorrencia(self, consultas: List[str], workers: int = 10):
        """Testa consultas concorrentes"""
        print(f"\n{'='*80}")
        print(f"⚡ TESTE DE CONCORRÊNCIA")
        print(f"{'='*80}")
        print(f"Consultas: {len(consultas)}")
        print(f"Workers: {workers}\n")
        
        start_total = time.time()
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self.testar_consulta, query): query 
                for query in consultas
            }
            
            for i, future in enumerate(as_completed(futures), 1):
                query = futures[future]
                try:
                    resultado = future.result()
                    status = "✅" if resultado['sucesso'] else "❌"
                    print(f"[{i}/{len(consultas)}] {status} '{query[:40]}...'")
                except Exception as e:
                    print(f"[{i}/{len(consultas)}] ❌ '{query[:40]}...' - {str(e)}")
        
        tempo_total = time.time() - start_total
        
        print(f"\n{'='*80}")
        print(f"⏱️  Tempo total: {tempo_total:.2f}s")
        print(f"📊 Throughput: {len(consultas)/tempo_total:.2f} req/s")
        print(f"{'='*80}\n")
    
    def teste_stress_volume(self, consulta_base: str, repeticoes: int = 100):
        """Testa volume de requisições"""
        print(f"\n{'='*80}")
        print(f"💪 TESTE DE STRESS - VOLUME")
        print(f"{'='*80}")
        print(f"Consulta base: '{consulta_base}'")
        print(f"Repetições: {repeticoes}\n")
        
        consultas = [f"{consulta_base} {i}" for i in range(repeticoes)]
        self.testar_suite("Stress Volume", consultas, verbose=False)
        
        print(f"Requisições por segundo: {repeticoes/self.stats['tempo_total']:.2f}")
    
    def gerar_relatorio(self):
        """Gera relatório completo dos testes"""
        print(f"\n{'='*80}")
        print(f"📊 RELATÓRIO FINAL DE TESTES")
        print(f"{'='*80}\n")
        
        # Estatísticas gerais
        print(f"📈 ESTATÍSTICAS GERAIS:")
        print(f"{'─'*80}")
        print(f"  Total de testes: {self.stats['total']}")
        print(f"  ✅ Sucessos: {self.stats['sucesso']} ({self.stats['sucesso']/self.stats['total']*100:.1f}%)")
        print(f"  ❌ Erros: {self.stats['erro']} ({self.stats['erro']/self.stats['total']*100:.1f}%)")
        print()
        
        # Estatísticas de tempo
        if self.stats['tempos']:
            print(f"⏱️  PERFORMANCE:")
            print(f"{'─'*80}")
            print(f"  Tempo total: {self.stats['tempo_total']:.2f}s")
            print(f"  Tempo médio: {statistics.mean(self.stats['tempos']):.3f}s")
            print(f"  Tempo mínimo: {self.stats['tempo_min']:.3f}s")
            print(f"  Tempo máximo: {self.stats['tempo_max']:.3f}s")
            print(f"  Mediana: {statistics.median(self.stats['tempos']):.3f}s")
            print(f"  Desvio padrão: {statistics.stdev(self.stats['tempos']):.3f}s" if len(self.stats['tempos']) > 1 else "")
            print(f"  Throughput: {self.stats['total']/self.stats['tempo_total']:.2f} req/s")
            print()
        
        # Top 10 mais lentas
        if self.resultados:
            print(f"🐌 TOP 10 CONSULTAS MAIS LENTAS:")
            print(f"{'─'*80}")
            top_lentas = sorted(self.resultados, key=lambda x: x.get('tempo', 0), reverse=True)[:10]
            for i, r in enumerate(top_lentas, 1):
                print(f"  {i}. {r['tempo']:.3f}s - '{r['query'][:60]}...'")
            print()
        
        # Erros
        if self.erros:
            print(f"❌ ERROS ENCONTRADOS ({len(self.erros)}):")
            print(f"{'─'*80}")
            for i, erro in enumerate(self.erros[:10], 1):  # Mostrar apenas os 10 primeiros
                print(f"  {i}. '{erro['query'][:50]}...'")
                print(f"     Status: {erro.get('status', 'N/A')}")
                print(f"     Erro: {erro.get('erro', 'N/A')[:100]}...")
                print()
        
        # Salvar relatório em arquivo
        relatorio_path = f"relatorio_testes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            json.dump({
                'stats': self.stats,
                'resultados': self.resultados,
                'erros': self.erros
            }, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Relatório salvo em: {relatorio_path}")
        print(f"{'='*80}\n")

# ============================================
# 🚀 SCRIPT PRINCIPAL
# ============================================

def main():
    """Executa todos os testes"""
    print(f"\n{'='*80}")
    print(f"🚀 INICIANDO TESTES DE STRESS DO SISTEMA RAG")
    print(f"{'='*80}")
    print(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"{'='*80}\n")
    
    # Verificar se API está online
    try:
        response = requests.get(f"{API_BASE_URL}/health/", timeout=5)
        if response.status_code == 200:
            print("✅ API está online e respondendo\n")
        else:
            print("⚠️  API respondeu mas com status diferente de 200\n")
    except Exception as e:
        print(f"❌ API não está respondendo: {e}")
        print("Certifique-se de que o servidor está rodando!")
        return
    
    # Criar instância do tester
    tester = RAGTester()
    
    # ========================================
    # EXECUTAR SUÍTES DE TESTE
    # ========================================
    
    # 1. Consultas Simples
    tester.testar_suite("1. CONSULTAS SIMPLES", TesteSuites.CONSULTAS_SIMPLES)
    
    # 2. Consultas com Características
    # tester.testar_suite("2. CONSULTAS COM CARACTERÍSTICAS", TesteSuites.CONSULTAS_CARACTERISTICAS)
    
    # 3. Consultas por Preço
    # tester.testar_suite("3. CONSULTAS POR PREÇO", TesteSuites.CONSULTAS_PRECO)
    
    # 4. Consultas por Categoria
    #  tester.testar_suite("4. CONSULTAS POR CATEGORIA", TesteSuites.CONSULTAS_CATEGORIA)
    
    # 5. Consultas Complexas
    #  tester.testar_suite("5. CONSULTAS COMPLEXAS", TesteSuites.CONSULTAS_COMPLEXAS)
    
    # 6. Consultas de Comparação
    #  tester.testar_suite("6. CONSULTAS DE COMPARAÇÃO", TesteSuites.CONSULTAS_COMPARACAO)
    
    # 7. Consultas de Disponibilidade
    #  tester.testar_suite("7. CONSULTAS DE DISPONIBILIDADE", TesteSuites.CONSULTAS_DISPONIBILIDADE)
    
    # 8. Consultas por Marca
    #  tester.testar_suite("8. CONSULTAS POR MARCA", TesteSuites.CONSULTAS_MARCA)
    
    # 9. Consultas de Recomendação
    #  tester.testar_suite("9. CONSULTAS DE RECOMENDAÇÃO", TesteSuites.CONSULTAS_RECOMENDACAO)
    
    # 10. Edge Cases
    #  tester.testar_suite("10. EDGE CASES", TesteSuites.CONSULTAS_EDGE_CASES)
    
    # 11. Consultas de Especificações
    #  tester.testar_suite("11. CONSULTAS DE ESPECIFICAÇÕES", TesteSuites.CONSULTAS_ESPECIFICACOES)
    
    # 12. Consultas Conversacionais
    #  tester.testar_suite("12. CONSULTAS CONVERSACIONAIS", TesteSuites.CONSULTAS_CONVERSACIONAIS)
    
    # 13. Consultas com Filtros Múltiplos
    #  tester.testar_suite("13. FILTROS MÚLTIPLOS", TesteSuites.CONSULTAS_FILTROS_MULTIPLOS)
    
    # 14. Consultas de Análise
    #  tester.testar_suite("14. CONSULTAS DE ANÁLISE", TesteSuites.CONSULTAS_ANALISE)
    
    # 15. Consultas Vagas
    #  tester.testar_suite("15. CONSULTAS VAGAS", TesteSuites.CONSULTAS_VAGAS)
    
    # ========================================
    # TESTES DE STRESS
    # ========================================
    
    # Teste de Concorrência
    print("\n" + "="*80)
    print("⚡ INICIANDO TESTES DE STRESS")
    print("="*80 + "\n")
    
    input("Pressione ENTER para iniciar teste de concorrência... ")
    tester.teste_concorrencia(TesteSuites.CONSULTAS_SIMPLES[:5], workers=5)
    
    # Teste de Volume
    input("Pressione ENTER para iniciar teste de volume (50 requisições)... ")
    tester.teste_stress_volume("teste stress", repeticoes=50)
    
    # ========================================
    # GERAR RELATÓRIO FINAL
    # ========================================
    
    tester.gerar_relatorio()
    
    print("\n🎉 TESTES CONCLUÍDOS!")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()