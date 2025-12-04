# conhecimento/rag/generator.py

import boto3
import json
from django.conf import settings


class ResponseGenerator:
    """Gerador de respostas usando Claude"""
    
    def __init__(self):
        self.bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.model_id = settings.BEDROCK_LLM_MODEL
    
    def generate(self, contexto: str, query: str) -> str:
        """
        Gera resposta usando Claude
        
        Args:
            contexto: Contexto formatado
            query: Pergunta original
            
        Returns:
            Resposta gerada
        """
        # Monta prompt
        system_prompt = f"""Você é um assistente da Paróquia São Francisco de Assis.

Sua função é ajudar as pessoas com informações sobre:
- Sacramentos (batismo, casamento, confissão, etc)
- Horários e localização
- Eventos e avisos
- Orientações pastorais

{contexto}

Responda de forma clara, objetiva e acolhedora. Use tom pastoral mas acessível."""

        # Chama Claude
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "system": system_prompt
        })
        
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            body=body
        )
        
        # Parse resposta
        response_body = json.loads(response['body'].read())
        resposta = response_body['content'][0]['text']
        
        return resposta