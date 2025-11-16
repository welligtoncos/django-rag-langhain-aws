import boto3
import json
import numpy as np
from unidecode import unidecode
from config.settings_rag import AWS_REGION, BEDROCK_EMBEDDING_MODEL


class Embeddings:
    """Gera embeddings usando Amazon Bedrock (Titan Embeddings)."""

    def __init__(self):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION,
        )
        self.model_id = BEDROCK_EMBEDDING_MODEL

    def _normalize(self, text: str) -> str:
        """Normaliza texto removendo acentos e convertendo para minúsculas"""
        if not isinstance(text, str):
            return ""
        return unidecode(text.lower().strip())

    def embed(self, text: str):
        """
        Gera embedding para o texto fornecido.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            np.array: Vetor de embedding (float32)
        """
        if not isinstance(text, str):
            raise ValueError("Texto para embedding deve ser uma string.")

        text = self._normalize(text)

        # Retorna vetor zero para textos vazios
        if len(text) == 0:
            return np.zeros(1024, dtype=np.float32)

        payload = {"inputText": text}

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload).encode("utf-8")
            )

            data = json.loads(response["body"].read())

            # Titan Embeddings v2 - formato atual
            if "embedding" in data:
                return np.array(data["embedding"], dtype=np.float32)

            # Titan Embeddings v1 - formato antigo
            if "output" in data and isinstance(data["output"], dict):
                if "embedding" in data["output"]:
                    return np.array(data["output"]["embedding"], dtype=np.float32)

            # Formatos alternativos
            if "embeddings" in data:
                return np.array(data["embeddings"], dtype=np.float32)

            if "vectors" in data:
                return np.array(data["vectors"], dtype=np.float32)

            raise RuntimeError(
                f"❌ Formato inesperado para o modelo {self.model_id} → {data}"
            )

        except self.client.exceptions.ValidationException as e:
            raise RuntimeError(f"❌ Erro de validação no Bedrock: {e}")

        except self.client.exceptions.ThrottlingException:
            raise RuntimeError(
                "❌ Serviço de Embeddings está sofrendo throttling. "
                "Reduza a taxa de requisições ou aguarde alguns segundos."
            )

        except Exception as e:
            raise RuntimeError(f"❌ Erro inesperado ao gerar embedding: {e}")
    
    def embed_batch(self, texts: list):
        """
        Gera embeddings para múltiplos textos.
        
        Args:
            texts: Lista de textos
            
        Returns:
            list: Lista de vetores numpy
        """
        return [self.embed(text) for text in texts]