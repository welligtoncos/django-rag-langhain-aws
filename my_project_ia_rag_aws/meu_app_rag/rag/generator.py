import boto3
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings_rag import (
    AWS_REGION, 
    BEDROCK_MODEL_ID,
    MAX_TOKENS,
    TEMPERATURE,
    TOP_P,
    HISTORICO_MAX
)


class ResponseGenerator:
    """Gerador de respostas usando Claude via AWS Bedrock."""

    def __init__(self):
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
        self.historico = []

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

        # Casos claros de vazio
        if ctx == "" or ctx.startswith("nenhum produto") or len(ctx) < 10:
            return True

        # Se não contém pelo menos 1 produto formatado
        if "id:" not in ctx and "nome:" not in ctx:
            return True

        return False

    def generate(self, query: str, context: str) -> str:
        """
        Gera resposta baseada na consulta e contexto fornecidos.
        
        Args:
            query: Pergunta do usuário
            context: Contexto dos produtos encontrados
            
        Returns:
            str: Resposta gerada pelo LLM
        """
        # Se contexto não tem produto → retorno automático
        if self._contexto_invalido(context):
            return (
                "Não encontrei produtos que correspondam à sua busca. "
                "Tente reformular sua pergunta ou buscar por outras características!"
            )

        # Prompt estruturado para o Claude
        system_prompt = f"""
Você é um assistente de compras especializado que responde EXCLUSIVAMENTE com base nos produtos fornecidos.

🎯 MISSÃO:
Ajudar o cliente a encontrar o produto ideal de forma clara, objetiva e útil.

📋 REGRAS OBRIGATÓRIAS:
1. ✅ Use APENAS informações dos produtos fornecidos no contexto
2. ✅ Seja objetivo, claro e amigável
3. ✅ Destaque promoções e boas avaliações quando relevante
4. ✅ Mencione se o estoque está baixo (menos de 10 unidades)
5. ✅ Compare produtos quando houver múltiplas opções
6. ❌ NUNCA invente produtos, marcas, preços ou características
7. ❌ NUNCA use conhecimento externo ou informações não fornecidas
8. ❌ Se a pergunta não puder ser respondida com o catálogo, diga:
   → "Não encontrei esse item específico no catálogo atual."

💡 DICAS:
- Formate preços claramente (ex: R$ 99,90)
- Seja conciso mas completo
- Foque no que o cliente perguntou
- Sugira alternativas quando apropriado

📦 CATÁLOGO DISPONÍVEL:

{context}
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]

        try:
            resposta = self.model.invoke(messages).content.strip()

            # Salvar no histórico (limitado)
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
            return f"Erro ao gerar resposta: {str(e)}"

    def clear_history(self):
        """Limpa o histórico de conversação"""
        self.historico = []

    def get_history(self):
        """Retorna o histórico de conversação"""
        return self.historico