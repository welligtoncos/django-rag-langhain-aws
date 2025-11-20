import boto3
import json
import time
import hashlib
import numpy as np
from typing import List, Union, Optional, Dict
from decimal import Decimal
from unidecode import unidecode
from django.core.cache import cache
from config.settings_rag import AWS_REGION, BEDROCK_EMBEDDING_MODEL


class Embeddings:
    """
    Gera embeddings usando Amazon Bedrock (Titan Embeddings).
    
    Funcionalidades:
    - Geração de embeddings com Titan Embeddings v2
    - Cache para reduzir custos e latência
    - Batch processing otimizado
    - Retry automático com backoff exponencial
    - Normalização avançada de texto
    - Métricas e estatísticas de uso
    """

    # Dimensões dos modelos Titan
    DIMENSOES = {
        "amazon.titan-embed-text-v1": 1536,
        "amazon.titan-embed-text-v2:0": 1024,
    }

    def __init__(self, use_cache: bool = True):
        """
        Inicializa cliente de embeddings.
        
        Args:
            use_cache: Se deve usar cache (padrão: True)
        """
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION,
        )
        self.model_id = BEDROCK_EMBEDDING_MODEL
        self.use_cache = use_cache
        self.dimensao = self.DIMENSOES.get(self.model_id, 1024)
        
        # Estatísticas
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "total_tokens": 0
        }
        
        print(f"✅ Embeddings inicializado: {self.model_id} ({self.dimensao}D)")

    def _normalize(self, text: str) -> str:
        """
        Normaliza texto para processamento.
        
        Aplica:
        - Conversão para minúsculas
        - Remoção de acentos
        - Remoção de caracteres especiais
        - Trim de espaços
        
        Args:
            text: Texto a normalizar
            
        Returns:
            str: Texto normalizado
        """
        if not isinstance(text, str):
            return ""
        
        # Conversão básica
        text = text.lower().strip()
        
        # Remove acentos
        text = unidecode(text)
        
        # Remove caracteres especiais excessivos (mantém pontuação básica)
        import re
        text = re.sub(r'[^\w\s.,!?-]', ' ', text)
        
        # Normaliza espaços
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def _get_cache_key(self, text: str) -> str:
        """
        Gera chave de cache para o texto.
        
        Args:
            text: Texto original
            
        Returns:
            str: Chave MD5 do texto normalizado
        """
        text_norm = self._normalize(text)
        hash_obj = hashlib.md5(text_norm.encode('utf-8'))
        return f"emb:{self.model_id}:{hash_obj.hexdigest()}"

    def _invoke_bedrock(
        self, 
        text: str, 
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> np.ndarray:
        """
        Invoca Bedrock com retry automático.
        
        Args:
            text: Texto para embedding
            max_retries: Número máximo de tentativas
            retry_delay: Delay inicial entre tentativas (segundos)
            
        Returns:
            np.ndarray: Vetor de embedding
            
        Raises:
            RuntimeError: Se todas as tentativas falharem
        """
        payload = {"inputText": text}
        
        for attempt in range(max_retries):
            try:
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(payload).encode("utf-8")
                )

                data = json.loads(response["body"].read())
                
                # Extrair embedding do formato retornado
                embedding = self._extract_embedding(data)
                
                # Validar dimensão
                if len(embedding) != self.dimensao:
                    raise RuntimeError(
                        f"❌ Dimensão incorreta: esperado {self.dimensao}, "
                        f"recebido {len(embedding)}"
                    )
                
                return embedding

            except self.client.exceptions.ThrottlingException:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Backoff exponencial
                    print(f"⚠️ Throttling detectado. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise RuntimeError(
                        "❌ Serviço de Embeddings está sobrecarregado. "
                        "Tente novamente mais tarde."
                    )

            except self.client.exceptions.ValidationException as e:
                raise RuntimeError(f"❌ Erro de validação no Bedrock: {e}")

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"⚠️ Erro na tentativa {attempt + 1}. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise RuntimeError(f"❌ Erro ao gerar embedding após {max_retries} tentativas: {e}")

    def _extract_embedding(self, data: dict) -> np.ndarray:
        """
        Extrai embedding de diferentes formatos de resposta.
        
        Args:
            data: Resposta JSON do Bedrock
            
        Returns:
            np.ndarray: Vetor de embedding
            
        Raises:
            RuntimeError: Se formato não for reconhecido
        """
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
            f"❌ Formato de resposta não reconhecido para {self.model_id}. "
            f"Chaves disponíveis: {list(data.keys())}"
        )

    def embed(
        self, 
        text: str,
        use_cache: Optional[bool] = None
    ) -> np.ndarray:
        """
        Gera embedding para um texto.
        
        Args:
            text: Texto para gerar embedding
            use_cache: Sobrescreve configuração de cache (opcional)
            
        Returns:
            np.ndarray: Vetor de embedding (float32)
            
        Raises:
            ValueError: Se texto não for string
            RuntimeError: Se houver erro na geração
        """
        # Validação de entrada
        if not isinstance(text, str):
            raise ValueError(f"Texto deve ser string, recebido: {type(text)}")

        # Incrementar contador
        self.stats["total_requests"] += 1

        # Normalizar texto
        text_norm = self._normalize(text)

        # Retorna vetor zero para textos vazios
        if not text_norm or len(text_norm) == 0:
            print("⚠️ Texto vazio, retornando vetor zero")
            return np.zeros(self.dimensao, dtype=np.float32)

        # Decidir sobre cache
        usar_cache = self.use_cache if use_cache is None else use_cache

        # Tentar cache
        if usar_cache:
            cache_key = self._get_cache_key(text)
            cached = cache.get(cache_key)
            
            if cached is not None:
                self.stats["cache_hits"] += 1
                return np.array(cached, dtype=np.float32)
            
            self.stats["cache_misses"] += 1

        # Gerar embedding
        try:
            embedding = self._invoke_bedrock(text_norm)
            
            # Salvar no cache (24 horas)
            if usar_cache:
                cache.set(cache_key, embedding.tolist(), 86400)
            
            # Atualizar estatísticas
            self.stats["total_tokens"] += len(text_norm.split())
            
            return embedding

        except Exception as e:
            self.stats["errors"] += 1
            raise

    def embed_batch(
        self, 
        texts: List[str],
        batch_size: int = 10,
        delay_between_batches: float = 0.5
    ) -> List[np.ndarray]:
        """
        Gera embeddings para múltiplos textos com rate limiting.
        
        Args:
            texts: Lista de textos
            batch_size: Tamanho do lote para processamento
            delay_between_batches: Delay entre lotes (segundos)
            
        Returns:
            list: Lista de vetores numpy
        """
        if not texts:
            return []

        embeddings = []
        total = len(texts)
        
        print(f"🔄 Processando {total} embeddings em lotes de {batch_size}...")
        
        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]
            batch_end = min(i + batch_size, total)
            
            print(f"   Lote {i//batch_size + 1}: itens {i+1}-{batch_end}/{total}")
            
            # Processar lote
            batch_embeddings = []
            for text in batch:
                try:
                    emb = self.embed(text)
                    batch_embeddings.append(emb)
                except Exception as e:
                    print(f"   ❌ Erro no texto '{text[:50]}...': {e}")
                    # Adicionar vetor zero em caso de erro
                    batch_embeddings.append(np.zeros(self.dimensao, dtype=np.float32))
            
            embeddings.extend(batch_embeddings)
            
            # Delay entre lotes (evitar throttling)
            if i + batch_size < total:
                time.sleep(delay_between_batches)
        
        print(f"✅ Processamento concluído: {len(embeddings)} embeddings gerados")
        
        return embeddings

    def embed_dict(self, data: Dict) -> np.ndarray:
        """
        Gera embedding para um dicionário (concatena valores relevantes).
        
        Args:
            data: Dicionário com dados do produto
            
        Returns:
            np.ndarray: Vetor de embedding
        """
        # Campos relevantes para embedding
        campos = [
            'nome', 'categoria', 'subcategoria', 
            'marca', 'descricao', 'especificacoes',
            'material', 'cor', 'tamanho'
        ]
        
        # Concatenar valores
        parts = []
        for campo in campos:
            valor = data.get(campo, '')
            if valor and str(valor).strip():
                parts.append(str(valor))
        
        texto = ' '.join(parts)
        return self.embed(texto)

    def similarity(
        self, 
        embedding1: np.ndarray, 
        embedding2: np.ndarray
    ) -> float:
        """
        Calcula similaridade de cosseno entre dois embeddings.
        
        Args:
            embedding1: Primeiro vetor
            embedding2: Segundo vetor
            
        Returns:
            float: Similaridade [0, 1]
        """
        # Normalizar vetores
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Similaridade de cosseno
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        
        # Garantir que está no intervalo [0, 1]
        return float(max(0.0, min(1.0, (similarity + 1) / 2)))

    def get_statistics(self) -> Dict:
        """
        Retorna estatísticas de uso.
        
        Returns:
            dict: Estatísticas detalhadas
        """
        cache_rate = 0.0
        if self.stats["total_requests"] > 0:
            cache_rate = (self.stats["cache_hits"] / self.stats["total_requests"]) * 100

        return {
            "modelo": self.model_id,
            "dimensao": self.dimensao,
            "total_requests": self.stats["total_requests"],
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "cache_rate": f"{cache_rate:.1f}%",
            "errors": self.stats["errors"],
            "total_tokens": self.stats["total_tokens"],
            "use_cache": self.use_cache
        }

    def clear_cache(self):
        """Limpa cache de embeddings"""
        # Django cache pattern
        from django.core.cache import cache as django_cache
        django_cache.clear()
        print("✅ Cache de embeddings limpo")

    def reset_statistics(self):
        """Reseta estatísticas de uso"""
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "total_tokens": 0
        }
        print("✅ Estatísticas resetadas")