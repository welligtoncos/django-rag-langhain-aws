import os
import re
import pickle
import hashlib
import numpy as np
from typing import List, Dict, Optional
from unidecode import unidecode
from django.core.exceptions import ImproperlyConfigured
from django.core.cache import cache
from .embeddings import Embeddings
from config.settings_rag import CATALOGO_PKL, VECTORS_PKL


class ProductRetriever:
    """
    RAG - Retrieval: Busca vetorial de produtos usando similaridade por embeddings.
    
    Funcionalidades:
    - Busca vetorial por similaridade semântica
    - Busca por categoria, preço, marca
    - Busca híbrida (vetorial + filtros)
    - Cache para performance
    - Estatísticas do catálogo
    """

    def __init__(self):
        """Inicializa o retriever e carrega dados"""
        self.embedding = Embeddings()
        
        # ✅ INICIALIZAR STATS
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0
        }
        
        self._load_data()
        print(f"✅ Retriever inicializado: {len(self.catalogo)} produtos carregados")

    def _load_data(self):
        """Carrega vetores e catálogo dos arquivos pickle"""
        # Validar existência dos arquivos
        if not os.path.exists(VECTORS_PKL):
            raise ImproperlyConfigured(
                f"❌ Arquivo {VECTORS_PKL} não encontrado. "
                f"Execute: python manage.py popular_embeddings --force"
            )

        if not os.path.exists(CATALOGO_PKL):
            raise ImproperlyConfigured(
                f"❌ Arquivo {CATALOGO_PKL} não encontrado. "
                f"Execute: python manage.py popular_embeddings --force"
            )

        # Carregar vetores
        try:
            with open(VECTORS_PKL, "rb") as f:
                data = pickle.load(f)

            self.product_ids = data["ids"]
            self.product_vectors = np.array(data["vectors"], dtype=np.float32)
            
            # Normalizar vetores uma vez (performance)
            norms = np.linalg.norm(self.product_vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1e-8
            self.product_vectors = self.product_vectors / norms
            
        except Exception as e:
            raise ImproperlyConfigured(f"❌ Erro ao carregar {VECTORS_PKL}: {e}")

        # Carregar catálogo
        try:
            with open(CATALOGO_PKL, "rb") as f:
                self.catalogo = pickle.load(f)
        except Exception as e:
            raise ImproperlyConfigured(f"❌ Erro ao carregar {CATALOGO_PKL}: {e}")

        if len(self.catalogo) == 0:
            print("⚠️ Aviso: catálogo carregado, mas está vazio!")

    def _normalize(self, text: str) -> str:
        """
        Normaliza texto para busca (remove acentos, lowercase, etc).
        
        Args:
            text: Texto a normalizar
            
        Returns:
            str: Texto normalizado
        """
        if not text:
            return ""
        
        text = text.lower().strip()
        text = unidecode(text)
        text = re.sub(r"[^a-z0-9 ]+", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _cosine_similarity(self, q: np.ndarray, M: np.ndarray) -> np.ndarray:
        """
        Calcula similaridade do cosseno entre vetor q e matriz M.
        Versão otimizada com vetores pré-normalizados.
        
        Args:
            q: Vetor de consulta (1D)
            M: Matriz de vetores normalizados (2D)
            
        Returns:
            np.array: Scores de similaridade [0, 1]
        """
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return np.zeros(M.shape[0])

        q = q / q_norm
        return np.dot(M, q)

    def retrieve(
        self, 
        query: str, 
        limit: int = 5,
        categoria: Optional[str] = None,
        preco_min: Optional[float] = None,
        preco_max: Optional[float] = None,
        marca: Optional[str] = None,
        em_estoque: bool = False,
        min_score: float = 0.0
    ) -> List[Dict]:
        """
        Busca produtos mais similares à consulta (busca híbrida).
        
        Combina busca vetorial com filtros tradicionais.
        
        Args:
            query: Texto da consulta
            limit: Número máximo de resultados
            categoria: Filtrar por categoria (opcional)
            preco_min: Preço mínimo (opcional)
            preco_max: Preço máximo (opcional)
            marca: Filtrar por marca (opcional)
            em_estoque: Apenas produtos em estoque (opcional)
            min_score: Score mínimo de similaridade (0-1)
            
        Returns:
            list: Lista de produtos ordenados por relevância
        """
        # Incrementar contador
        self.stats["total_requests"] += 1

        # ✅ CRIAR CHAVE DE CACHE COM HASH MD5
        cache_key_raw = f"{query}:{limit}:{categoria}:{preco_min}:{preco_max}:{marca}:{em_estoque}"
        cache_key_hash = hashlib.md5(cache_key_raw.encode('utf-8')).hexdigest()
        cache_key = f"retrieve_{cache_key_hash}"
        
        # Tentar obter do cache
        cached_result = cache.get(cache_key)
        if cached_result:
            self.stats["cache_hits"] += 1
            return cached_result
        
        self.stats["cache_misses"] += 1

        # Normalizar consulta
        query_norm = self._normalize(query)

        # Gerar embedding
        try:
            query_vector = np.array(
                self.embedding.embed(query_norm), 
                dtype=np.float32
            )
        except Exception as e:
            print(f"❌ Erro ao gerar embedding: {e}")
            self.stats["errors"] += 1
            return []

        # Calcular similaridade
        scores = self._cosine_similarity(query_vector, self.product_vectors)

        # Aplicar filtros
        filtered_indices = []
        for idx in range(len(self.product_ids)):
            prod_id = self.product_ids[idx]
            
            if prod_id not in self.catalogo:
                continue

            produto = self.catalogo[prod_id]
            score = scores[idx]

            # Filtro de score mínimo
            if score < min_score:
                continue

            # Filtros opcionais
            if categoria and produto.get('categoria', '').lower() != categoria.lower():
                continue

            if preco_min and produto.get('preco', 0) < preco_min:
                continue

            if preco_max and produto.get('preco', float('inf')) > preco_max:
                continue

            if marca and produto.get('marca', '').lower() != marca.lower():
                continue

            if em_estoque and produto.get('estoque', 0) <= 0:
                continue

            filtered_indices.append((idx, score))

        # Ordenar por score e limitar
        filtered_indices.sort(key=lambda x: x[1], reverse=True)
        top_indices = filtered_indices[:limit]

        # Montar resultados
        resultados = []
        for idx, score in top_indices:
            prod_id = self.product_ids[idx]
            produto = dict(self.catalogo[prod_id])
            
            # ✅ VALIDAR ID NO BANCO (evita erro 404)
            try:
                from meu_app_rag.models import Produto
                produto_db = Produto.objects.filter(id=prod_id).first()
                
                if produto_db:
                    produto["id"] = produto_db.id
                else:
                    # Buscar por nome se ID não existir
                    produto_db = Produto.objects.filter(nome=produto.get('nome')).first()
                    if produto_db:
                        produto["id"] = produto_db.id
                    else:
                        print(f"⚠️ Produto não encontrado: {produto.get('nome')}")
                        continue
                        
            except Exception as e:
                print(f"⚠️ Erro ao validar produto: {e}")
                continue
            
            produto["score"] = float(score)
            produto["score_percentual"] = f"{float(score) * 100:.1f}%"
            resultados.append(produto)

        # Salvar no cache por 5 minutos
        try:
            cache.set(cache_key, resultados, 300)
        except Exception as e:
            print(f"⚠️ Erro ao salvar cache: {e}")

        return resultados

    def retrieve_by_category(
        self, 
        categoria: str, 
        limit: int = 10,
        preco_min: Optional[float] = None,
        preco_max: Optional[float] = None
    ) -> List[Dict]:
        """
        Busca produtos por categoria (sem busca vetorial).
        
        Args:
            categoria: Nome da categoria
            limit: Número máximo de resultados
            preco_min: Preço mínimo (opcional)
            preco_max: Preço máximo (opcional)
            
        Returns:
            list: Lista de produtos da categoria
        """
        resultados = []
        
        for prod_id, produto in self.catalogo.items():
            # Filtro de categoria
            if produto.get('categoria', '').lower() != categoria.lower():
                continue

            # Filtros de preço
            if preco_min and produto.get('preco', 0) < preco_min:
                continue

            if preco_max and produto.get('preco', float('inf')) > preco_max:
                continue

            produto_copy = dict(produto)
            produto_copy["score"] = 1.0
            produto_copy["score_percentual"] = "100.0%"
            resultados.append(produto_copy)
            
            if len(resultados) >= limit:
                break
        
        return resultados

    def retrieve_by_price_range(
        self, 
        preco_min: float, 
        preco_max: float, 
        limit: int = 10,
        categoria: Optional[str] = None
    ) -> List[Dict]:
        """
        Busca produtos por faixa de preço.
        
        Args:
            preco_min: Preço mínimo
            preco_max: Preço máximo
            limit: Número máximo de resultados
            categoria: Filtrar por categoria (opcional)
            
        Returns:
            list: Lista de produtos na faixa de preço
        """
        resultados = []
        
        for prod_id, produto in self.catalogo.items():
            preco = produto.get('preco', 0)
            
            if preco < preco_min or preco > preco_max:
                continue

            if categoria and produto.get('categoria', '').lower() != categoria.lower():
                continue

            produto_copy = dict(produto)
            produto_copy["score"] = 1.0
            produto_copy["score_percentual"] = "100.0%"
            resultados.append(produto_copy)
            
            if len(resultados) >= limit:
                break
        
        # Ordenar por preço
        resultados.sort(key=lambda x: x.get('preco', 0))
        
        return resultados[:limit]

    def retrieve_by_ids(self, product_ids: List[int]) -> List[Dict]:
        """
        Busca produtos por lista de IDs.
        
        Args:
            product_ids: Lista de IDs de produtos
            
        Returns:
            list: Lista de produtos encontrados
        """
        resultados = []
        
        for prod_id in product_ids:
            if prod_id in self.catalogo:
                produto = dict(self.catalogo[prod_id])
                produto["score"] = 1.0
                produto["score_percentual"] = "100.0%"
                resultados.append(produto)
        
        return resultados

    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """
        Busca produto por ID único.
        
        Args:
            product_id: ID do produto
            
        Returns:
            dict ou None: Produto encontrado ou None
        """
        produto = self.catalogo.get(product_id)
        if produto:
            produto_copy = dict(produto)
            produto_copy["score"] = 1.0
            produto_copy["score_percentual"] = "100.0%"
            return produto_copy
        return None

    def get_similar_products(
        self, 
        product_id: int, 
        limit: int = 5,
        mesma_categoria: bool = True
    ) -> List[Dict]:
        """
        Busca produtos similares a um produto específico.
        
        Args:
            product_id: ID do produto de referência
            limit: Número de produtos similares
            mesma_categoria: Apenas da mesma categoria
            
        Returns:
            list: Produtos similares
        """
        # Encontrar índice do produto
        try:
            idx = list(self.product_ids).index(product_id)
        except ValueError:
            return []

        # Vetor do produto
        product_vector = self.product_vectors[idx]

        # Calcular similaridade com todos
        scores = self._cosine_similarity(product_vector, self.product_vectors)

        # Remover o próprio produto
        scores[idx] = -1

        # Filtrar por categoria se necessário
        if mesma_categoria:
            categoria_ref = self.catalogo[product_id].get('categoria')
            for i in range(len(scores)):
                pid = self.product_ids[i]
                if pid in self.catalogo:
                    if self.catalogo[pid].get('categoria') != categoria_ref:
                        scores[i] = -1

        # Top-N
        top_idx = np.argsort(scores)[::-1][:limit]

        resultados = []
        for idx in top_idx:
            if scores[idx] < 0:
                continue

            prod_id = self.product_ids[idx]
            if prod_id in self.catalogo:
                produto = dict(self.catalogo[prod_id])
                produto["score"] = float(scores[idx])
                produto["score_percentual"] = f"{float(scores[idx]) * 100:.1f}%"
                resultados.append(produto)

        return resultados

    def get_statistics(self) -> Dict:
        """
        Retorna estatísticas detalhadas do catálogo.
        
        Returns:
            dict: Estatísticas completas
        """
        if not self.catalogo:
            return {
                "total_produtos": 0,
                "total_embeddings": 0,
                "dimensao_vetores": 0,
                "categorias": [],
                "marcas": [],
                "preco_minimo": 0,
                "preco_maximo": 0,
                "preco_medio": 0,
                "produtos_em_estoque": 0,
                "produtos_com_imagem": 0,
                "avaliacao_media": 0
            }

        # Estatísticas de preço
        precos = [p.get('preco', 0) for p in self.catalogo.values() if p.get('preco')]
        
        # Categorias e marcas
        categorias = set(p.get('categoria', '') for p in self.catalogo.values() if p.get('categoria'))
        marcas = set(p.get('marca', '') for p in self.catalogo.values() if p.get('marca'))
        
        # Estoque
        em_estoque = sum(1 for p in self.catalogo.values() if p.get('estoque', 0) > 0)
        
        # Imagens
        com_imagem = sum(
            1 for p in self.catalogo.values() 
            if p.get('imagem') or p.get('imagem_url')
        )
        
        # Avaliações
        avaliacoes = [p.get('avaliacao', 0) for p in self.catalogo.values() if p.get('avaliacao')]

        return {
            "total_produtos": len(self.catalogo),
            "total_embeddings": len(self.product_vectors),
            "dimensao_vetores": self.product_vectors.shape[1] if len(self.product_vectors) > 0 else 0,
            "categorias": sorted(list(categorias)),
            "total_categorias": len(categorias),
            "marcas": sorted(list(marcas)),
            "total_marcas": len(marcas),
            "preco_minimo": float(min(precos)) if precos else 0,
            "preco_maximo": float(max(precos)) if precos else 0,
            "preco_medio": float(sum(precos) / len(precos)) if precos else 0,
            "produtos_em_estoque": em_estoque,
            "produtos_com_imagem": com_imagem,
            "avaliacao_media": float(sum(avaliacoes) / len(avaliacoes)) if avaliacoes else 0,
            "arquivos": {
                "catalogo": CATALOGO_PKL,
                "vectors": VECTORS_PKL
            }
        }

    def clear_cache(self):
        """Limpa cache de buscas"""
        cache.clear()
        print("✅ Cache limpo")

    def reload_data(self):
        """Recarrega dados dos arquivos pickle"""
        self._load_data()
        self.clear_cache()
        print("✅ Dados recarregados")