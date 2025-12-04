# conhecimento/rag/embeddings.py

import boto3
import json
import numpy as np
from django.conf import settings


class Embeddings:
    """Gerador de embeddings usando Amazon Titan"""
    
    def __init__(self):
        self.bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.model_id = settings.BEDROCK_EMBEDDING_MODEL
    
    def embed(self, text: str) -> np.ndarray:
        """
        Gera embedding para texto
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Array numpy com embedding (1024 dimensões)
        """
        if not text or not text.strip():
            raise ValueError("Texto vazio")
        
        # Limita tamanho (Titan aceita até ~8k tokens)
        text = text[:25000]
        
        # Chama Bedrock
        body = json.dumps({
            "inputText": text
        })
        
        response = self.bedrock.invoke_model(
            modelId=self.model_id,
            body=body,
            contentType='application/json',
            accept='application/json'
        )
        
        # Parse resposta
        response_body = json.loads(response['body'].read())
        embedding = response_body.get('embedding')
        
        if not embedding:
            raise ValueError("Embedding não retornado pela API")
        
        return np.array(embedding, dtype=np.float32)