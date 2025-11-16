import os
import re
import pickle
import numpy as np
from unidecode import unidecode
from django.core.exceptions import ImproperlyConfigured
from .embeddings import Embeddings
from config.settings_rag import CATALOGO_PKL, VECTORS_PKL


class ProductRetriever:
    """RAG - Busca vetorial de produtos usando similaridade por embeddings"""

    def __init__(self):
        self.embedding = Embeddings()
        
        # Validar existência dos arquivos
        if not os.path.exists(VECTORS_PKL):
            raise ImproperlyConfigured(
                f"❌ Arquivo {VECTORS_PKL} não encontrado. "
                f"Execute: python manage.py popular_embeddings"
            )

        if not os.path.exists(CATALOGO_PKL):
            raise ImproperlyConfigured(
                f"❌ Arquivo {CATALOGO_PKL} não encontrado. "
                f"Execute: python manage.py popular_embeddings"
            )

        # Carregar vetores
        with open(VECTORS_PKL, "rb") as f:
            data = pickle.load(f)

        self.product_ids = data["ids"]
        self.product_vectors = np.array(data["vectors"], dtype=np.float32)

        # Carregar catálogo
        with open(CATALOGO_PKL, "rb") as f:
            self.catalogo = pickle.load(f)

        if len(self.catalogo) == 0:
            print("⚠️ Aviso: catálogo carregado, mas está vazio!")

    def _normalize(self, text: str) -> str:
        """Normaliza texto para busca"""
        text = text.lower().strip()
        text = unidecode(text)
        text = re.sub(r"[^a-z0-9 ]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _cosine_similarity(self, q, M):
        """
        Calcula similaridade do cosseno entre vetor q e matriz M.
        
        Args:
            q: Vetor de consulta (1D)
            M: Matriz de vetores (2D)
            
        Returns:
            np.array: Scores de similaridade
        """
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return np.zeros(M.shape[0])

        q = q / q_norm
        M_norm = np.linalg.norm(M, axis=1, keepdims=True)
        M_norm[M_norm == 0] = 1e-8  # Evita divisão por zero

        M = M / M_norm
        return np.dot(M, q)

    def retrieve(self, query: str, limit: int = 5):
        """
        Busca produtos mais similares à consulta.
        
        Args:
            query: Texto da consulta
            limit: Número máximo de resultados
            
        Returns:
            list: Lista de produtos com score de similaridade
        """
        # Normalizar consulta
        query_norm = self._normalize(query)

        # Gerar embedding
        query_vector = np.array(
            self.embedding.embed(query_norm), 
            dtype=np.float32
        )

        # Calcular similaridade
        scores = self._cosine_similarity(query_vector, self.product_vectors)

        # Selecionar top-N
        top_idx = np.argsort(scores)[::-1][:limit]

        resultados = []
        for idx in top_idx:
            prod_id = self.product_ids[idx]

            if prod_id not in self.catalogo:
                continue  # Failsafe

            produto = dict(self.catalogo.get(prod_id))
            produto["score"] = float(scores[idx])

            resultados.append(produto)

        return resultados

    def retrieve_by_category(self, categoria: str, limit: int = 10):
        """
        Busca produtos por categoria.
        
        Args:
            categoria: Nome da categoria
            limit: Número máximo de resultados
            
        Returns:
            list: Lista de produtos da categoria
        """
        resultados = []
        
        for prod_id, produto in self.catalogo.items():
            if produto.get('categoria', '').lower() == categoria.lower():
                produto_copy = dict(produto)
                produto_copy["score"] = 1.0  # Score máximo para busca exata
                resultados.append(produto_copy)
                
                if len(resultados) >= limit:
                    break
        
        return resultados

    def get_product_by_id(self, product_id: int):
        """
        Busca produto por ID.
        
        Args:
            product_id: ID do produto
            
        Returns:
            dict ou None: Produto encontrado ou None
        """
        return self.catalogo.get(product_id)

    def get_statistics(self):
        """
        Retorna estatísticas do catálogo.
        
        Returns:
            dict: Estatísticas do catálogo
        """
        if not self.catalogo:
            return {
                "total_produtos": 0,
                "categorias": [],
                "preco_minimo": 0,
                "preco_maximo": 0,
                "preco_medio": 0
            }

        precos = [p.get('preco', 0) for p in self.catalogo.values() if p.get('preco')]
        categorias = set(p.get('categoria', '') for p in self.catalogo.values() if p.get('categoria'))

        return {
            "total_produtos": len(self.catalogo),
            "categorias": sorted(list(categorias)),
            "preco_minimo": min(precos) if precos else 0,
            "preco_maximo": max(precos) if precos else 0,
            "preco_medio": sum(precos) / len(precos) if precos else 0
        }   