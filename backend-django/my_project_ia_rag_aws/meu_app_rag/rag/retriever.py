# conhecimento/rag/retriever.py

import numpy as np
import logging
from typing import List, Dict, Optional
from unidecode import unidecode
import re
from .embeddings import Embeddings
from ..models import KnowledgeBase, Documento
from django.utils import timezone

from .. import models

from django.db.models import Q

 

logger = logging.getLogger(__name__)


class MultiBaseRetriever:
    """Retriever para múltiplas bases de conhecimento"""
    
    def __init__(self):
        self.embeddings = Embeddings()
    
    def retrieve(
        self,
        query: str,
        bases: Optional[List[str]] = None,
        limit: int = 5,
        min_score: float = 0.0
    ) -> List[Dict]:
        """
        Busca documentos em múltiplas bases
        
        Args:
            query: Consulta do usuário
            bases: Lista de slugs (None = todas ativas)
            limit: Número máximo de resultados
            min_score: Score mínimo
            
        Returns:
            Lista de documentos com scores
        """
        logger.info(f"Buscando: '{query}'")
        
        # 1. Normaliza query
        query_norm = self._normalize(query)
        
        # 2. Gera embedding
        query_embedding = self.embeddings.embed(query_norm)
        
        # 3. Filtra bases
        queryset = KnowledgeBase.objects.filter(ativo=True)
        if bases:
            queryset = queryset.filter(slug__in=bases)
        
        bases_ativas = list(queryset)
        
        if not bases_ativas:
            logger.warning("Nenhuma base ativa")
            return []
        
        # 4. Busca documentos válidos
        agora = timezone.now()
        documentos = []
        
        for base in bases_ativas:
            docs = Documento.objects.filter(
                base=base,
                status='ativo',
                embedding__isnull=False
            ).filter(
                models.Q(data_inicio__isnull=True) | models.Q(data_inicio__lte=agora)
            ).filter(
                models.Q(data_fim__isnull=True) | models.Q(data_fim__gte=agora)
            )
            
            for doc in docs:
                documentos.append({
                    'documento': doc,
                    'base': base,
                    'embedding': np.array(doc.embedding, dtype=np.float32)
                })
        
        if not documentos:
            logger.warning("Nenhum documento encontrado")
            return []
        
        logger.info(f"{len(documentos)} documentos disponíveis")
        
        # 5. Calcula similaridades
        for item in documentos:
            score = self._cosine_similarity(
                query_embedding,
                item['embedding']
            )
            
            # Boost por prioridade da base
            boost = 1.0 + (item['base'].prioridade / 100.0)
            score = score * boost
            
            item['score'] = float(score)
        
        # 6. Filtra por score mínimo
        documentos = [d for d in documentos if d['score'] >= min_score]
        
        # 7. Ordena e limita
        documentos.sort(key=lambda x: x['score'], reverse=True)
        documentos = documentos[:limit]
        
        # 8. Formata resultado
        resultados = []
        for item in documentos:
            doc = item['documento']
            base = item['base']
            
            resultados.append({
                'id': doc.id,
                'titulo': doc.titulo,
                'conteudo': doc.conteudo,
                'categoria': doc.categoria,
                'tags': doc.tags,
                'base': {
                    'nome': base.nome,
                    'slug': base.slug,
                    'icone': base.icone,
                    'tipo': base.tipo
                },
                'score': item['score'],
                'data_fim': doc.data_fim,
                'criado_em': doc.criado_em
            })
        
        logger.info(f"✅ {len(resultados)} documentos retornados")
        return resultados
    
    def _normalize(self, text: str) -> str:
        """Normaliza texto"""
        text = text.lower()
        text = unidecode(text)
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calcula similaridade do cosseno"""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))