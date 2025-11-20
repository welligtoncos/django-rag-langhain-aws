import boto3
from typing import List, Dict, Optional
from decimal import Decimal
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from config.settings_rag import (
    AWS_REGION, 
    BEDROCK_MODEL_ID,
    MAX_TOKENS,
    TEMPERATURE,
    TOP_P,
    HISTORICO_MAX
)


class ResponseGenerator:
    """
    RAG - Generation: Gerador de respostas usando Claude via AWS Bedrock.
    
    Funcionalidades:
    - Geração de respostas contextualizadas
    - Histórico de conversação
    - Diferentes modos de resposta (rápida, detalhada)
    - Formatação inteligente de produtos
    - Tratamento de edge cases
    """

    def __init__(self):
        """Inicializa o gerador com cliente AWS Bedrock"""
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name=AWS_REGION
        )

        self.model = ChatBedrock(
            model_id=BEDROCK_MODEL_ID,
            client=self.client,
            model_kwargs={
                "max_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "top_p": TOP_P
            }
        )

        # Histórico de conversação
        self.historico: List[Dict[str, str]] = []
        
        print(f"✅ Generator inicializado: {BEDROCK_MODEL_ID}")

    def _contexto_invalido(self, contexto: str) -> bool:
        """
        Verifica se o contexto está vazio ou inválido.
        
        Args:
            contexto: Contexto gerado pelo augmenter
            
        Returns:
            bool: True se o contexto é inválido
        """
        if not contexto:
            return True

        ctx = contexto.strip().lower()

        # Casos claros de contexto vazio
        if (
            ctx == "" 
            or ctx.startswith("nenhum produto") 
            or ctx.startswith("nenhuma informação")
            or len(ctx) < 20
        ):
            return True

        # Se não contém pelo menos 1 produto formatado
        if "id:" not in ctx and "nome:" not in ctx and "produto" not in ctx:
            return True

        return False

    def _formatar_preco(self, preco: float) -> str:
        """
        Formata preço para exibição em Real brasileiro.
        
        Args:
            preco: Valor numérico do preço
            
        Returns:
            str: Preço formatado (ex: R$ 99,90)
        """
        if isinstance(preco, (Decimal, float, int)):
            return f"R$ {float(preco):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return str(preco)

    def _criar_system_prompt(self, modo: str = "normal") -> str:
        """
        Cria prompt do sistema baseado no modo.
        
        Args:
            modo: Tipo de resposta ('normal', 'rapida', 'detalhada')
            
        Returns:
            str: System prompt formatado
        """
        base_prompt = """
Você é um assistente de compras virtual especializado, amigável e prestativo.

🎯 SUA MISSÃO:
Ajudar clientes a encontrar produtos ideais usando APENAS o catálogo fornecido.

📋 REGRAS FUNDAMENTAIS:
1. ✅ USE APENAS informações dos produtos no contexto fornecido
2. ✅ Seja claro, objetivo e amigável (tom conversacional)
3. ✅ Mencione preços, marcas e características relevantes
4. ✅ Destaque promoções quando houver preço promocional
5. ✅ Destaque avaliações altas (≥4.5 estrelas)
6. ✅ Avise se estoque está baixo (<10 unidades)
7. ✅ Compare produtos quando houver múltiplas opções
8. ❌ NUNCA invente produtos, preços ou informações
9. ❌ NUNCA use conhecimento externo ao catálogo
10. ❌ Se não encontrar, seja honesto: "Não encontrei esse produto."

💡 FORMATO DE RESPOSTA:
"""

        if modo == "rapida":
            base_prompt += """
- Seja MUITO CONCISO (2-3 frases no máximo)
- Liste apenas nome, preço e 1 característica chave
- Use bullet points para múltiplos produtos
"""
        elif modo == "detalhada":
            base_prompt += """
- Seja COMPLETO e DESCRITIVO
- Inclua: preço, marca, características, estoque, avaliações
- Compare vantagens entre produtos
- Sugira alternativas quando apropriado
- Use emojis moderadamente para destacar pontos importantes
"""
        else:  # normal
            base_prompt += """
- Seja EQUILIBRADO entre conciso e informativo
- Mencione: preço, marca e 2-3 características principais
- Destaque o melhor custo-benefício
- Use tom amigável e profissional
"""

        base_prompt += """

📝 EXEMPLOS DE BOAS RESPOSTAS:

❓ "Quero uma camiseta branca"
✅ "Encontrei a Camiseta Básica Branca da BasicWear por R$ 39,90. É 100% algodão, 
    tem ótima avaliação (4.3⭐) e está disponível no tamanho M com 150 unidades 
    em estoque."

❓ "Tênis até 200 reais"
✅ "Tenho o Tênis Corrida Pro Run em PROMOÇÃO! De R$ 199,90 por R$ 149,90 🔥
    É da SportPro, tem solado EVA e avaliação excelente (4.8⭐). 
    30 unidades disponíveis no tamanho 42."

❓ "Perfume importado"
✅ "O Perfume Masculino Intense da FragrancePro é perfeito! R$ 289,90 pelos 100ml.
    Tem notas amadeiradas e cítricas, concentração de 15% e avaliação 4.9⭐. 
    É sofisticado e de longa duração. Estoque baixo: apenas 8 unidades!"

🚫 NUNCA FAÇA:
❌ "Temos também o Tênis Nike Air Max..." (produto não está no catálogo)
❌ "Este produto é o melhor do mercado..." (opinião não baseada em dados)
❌ "Entrega em 2 dias..." (info não fornecida no catálogo)
"""

        return base_prompt

    def generate(
        self, 
        query: str, 
        context: str,
        modo: str = "normal",
        incluir_historico: bool = False
    ) -> str:
        """
        Gera resposta baseada na consulta e contexto.
        
        Args:
            query: Pergunta do usuário
            context: Contexto dos produtos encontrados (do augmenter)
            modo: Tipo de resposta ('normal', 'rapida', 'detalhada')
            incluir_historico: Se deve incluir histórico da conversa
            
        Returns:
            str: Resposta gerada pelo LLM
        """
        # Validar modo
        if modo not in ['normal', 'rapida', 'detalhada']:
            modo = 'normal'

        # Se contexto não tem produto → retorno automático
        if self._contexto_invalido(context):
            return (
                "😔 Não encontrei produtos que correspondam à sua busca.\n\n"
                "💡 Dicas:\n"
                "• Tente usar termos mais gerais (ex: 'tênis' em vez de 'tênis Nike Air')\n"
                "• Verifique a ortografia\n"
                "• Busque por categoria (Roupas, Eletrônicos, Beleza, etc.)\n"
                "• Pergunte sobre faixas de preço"
            )

        # Criar prompt do sistema
        system_prompt = self._criar_system_prompt(modo)
        
        # Adicionar catálogo ao prompt
        system_prompt += f"\n\n📦 CATÁLOGO DISPONÍVEL:\n\n{context}"

        # Construir mensagens
        messages = [SystemMessage(content=system_prompt)]

        # Adicionar histórico se solicitado
        if incluir_historico and self.historico:
            for msg in self.historico[-HISTORICO_MAX * 2:]:
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    messages.append(AIMessage(content=msg['content']))

        # Adicionar consulta atual
        messages.append(HumanMessage(content=query))

        try:
            # Invocar modelo
            resposta = self.model.invoke(messages).content.strip()

            # Pós-processar resposta
            resposta = self._pos_processar_resposta(resposta)

            # Salvar no histórico
            self.historico.append({
                "role": "user",
                "content": query
            })
            self.historico.append({
                "role": "assistant",
                "content": resposta
            })

            # Manter apenas últimas N interações
            if len(self.historico) > HISTORICO_MAX * 2:
                self.historico = self.historico[-HISTORICO_MAX * 2:]

            return resposta

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Erro ao gerar resposta: {error_msg}")
            
            return (
                "❌ Desculpe, houve um erro ao processar sua solicitação.\n\n"
                f"Detalhes técnicos: {error_msg}\n\n"
                "Por favor, tente novamente em alguns instantes."
            )

    def _pos_processar_resposta(self, resposta: str) -> str:
        """
        Pós-processa a resposta para melhorar formatação.
        
        Args:
            resposta: Resposta bruta do LLM
            
        Returns:
            str: Resposta formatada
        """
        # Remove espaços extras
        resposta = resposta.strip()
        
        # Remove quebras de linha excessivas
        while "\n\n\n" in resposta:
            resposta = resposta.replace("\n\n\n", "\n\n")
        
        # Garante que não termine com pontos múltiplos
        while resposta.endswith(".."):
            resposta = resposta[:-1]
        
        return resposta

    def generate_rapida(self, query: str, context: str) -> str:
        """
        Gera resposta rápida e concisa (modo express).
        
        Args:
            query: Pergunta do usuário
            context: Contexto dos produtos
            
        Returns:
            str: Resposta concisa
        """
        return self.generate(query, context, modo='rapida')

    def generate_detalhada(self, query: str, context: str) -> str:
        """
        Gera resposta detalhada e completa.
        
        Args:
            query: Pergunta do usuário
            context: Contexto dos produtos
            
        Returns:
            str: Resposta detalhada
        """
        return self.generate(query, context, modo='detalhada')

    def generate_com_historico(self, query: str, context: str) -> str:
        """
        Gera resposta considerando histórico de conversação.
        
        Args:
            query: Pergunta do usuário
            context: Contexto dos produtos
            
        Returns:
            str: Resposta contextualizada com histórico
        """
        return self.generate(query, context, incluir_historico=True)

    def generate_comparacao(
        self, 
        query: str, 
        produtos: List[Dict]
    ) -> str:
        """
        Gera comparação entre produtos específicos.
        
        Args:
            query: Pergunta sobre comparação
            produtos: Lista de produtos a comparar
            
        Returns:
            str: Comparação detalhada
        """
        # Criar contexto de comparação
        context_parts = []
        for i, p in enumerate(produtos, 1):
            context_parts.append(
                f"\n{'='*50}\n"
                f"PRODUTO {i}:\n"
                f"Nome: {p.get('nome', 'N/A')}\n"
                f"Preço: {self._formatar_preco(p.get('preco', 0))}\n"
                f"Marca: {p.get('marca', 'N/A')}\n"
                f"Avaliação: {p.get('avaliacao', 0)}⭐ ({p.get('num_avaliacoes', 0)} avaliações)\n"
                f"Estoque: {p.get('estoque', 0)} unidades\n"
                f"Descrição: {p.get('descricao', 'N/A')}\n"
            )
            
            if p.get('preco_promocional'):
                context_parts.append(
                    f"🔥 PROMOÇÃO: {self._formatar_preco(p['preco_promocional'])}\n"
                )
        
        context = "\n".join(context_parts)
        
        # Prompt específico para comparação
        query_comparacao = f"""
Compare os produtos listados focando em:
1. Melhor custo-benefício
2. Diferenças de qualidade/avaliação
3. Preço e promoções
4. Disponibilidade (estoque)

Consulta original: {query}

Faça uma comparação clara e objetiva ajudando na decisão de compra.
"""
        
        return self.generate_detalhada(query_comparacao, context)

    def clear_history(self):
        """Limpa o histórico de conversação"""
        self.historico = []
        print("✅ Histórico limpo")

    def get_history(self) -> List[Dict[str, str]]:
        """
        Retorna o histórico de conversação.
        
        Returns:
            list: Lista de mensagens do histórico
        """
        return self.historico

    def get_history_formatted(self) -> str:
        """
        Retorna histórico formatado para visualização.
        
        Returns:
            str: Histórico formatado
        """
        if not self.historico:
            return "Nenhum histórico disponível."
        
        formatted = []
        for msg in self.historico:
            role = "👤 Usuário" if msg['role'] == 'user' else "🤖 Assistente"
            formatted.append(f"{role}: {msg['content']}\n")
        
        return "\n".join(formatted)

    def get_statistics(self) -> Dict:
        """
        Retorna estatísticas do gerador.
        
        Returns:
            dict: Estatísticas de uso
        """
        total_mensagens = len(self.historico)
        mensagens_usuario = sum(1 for m in self.historico if m['role'] == 'user')
        mensagens_assistente = sum(1 for m in self.historico if m['role'] == 'assistant')
        
        return {
            "total_mensagens": total_mensagens,
            "mensagens_usuario": mensagens_usuario,
            "mensagens_assistente": mensagens_assistente,
            "modelo": BEDROCK_MODEL_ID,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "historico_max": HISTORICO_MAX
        }