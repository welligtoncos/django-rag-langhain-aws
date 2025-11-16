import time
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from django.core.exceptions import ImproperlyConfigured

from .models import Produto
from .serializers import (
    ProdutoSerializer,
    ProdutoListSerializer,
    RAGQuerySerializer,
    RAGResponseSerializer
)
from .rag.retriever import ProductRetriever
from .rag.augmenter import ContextAugmenter
from .rag.generator import ResponseGenerator


class ProdutoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operações CRUD de produtos.
    
    Endpoints:
    - GET /api/produtos/ - Lista todos os produtos
    - POST /api/produtos/ - Cria novo produto
    - GET /api/produtos/{id}/ - Detalhe de um produto
    - PUT /api/produtos/{id}/ - Atualiza produto
    - DELETE /api/produtos/{id}/ - Remove produto
    """
    
    queryset = Produto.objects.all()
    serializer_class = ProdutoSerializer
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProdutoListSerializer
        return ProdutoSerializer
    
    @extend_schema(
        description="Lista produtos com filtros opcionais",
        parameters=[
            OpenApiParameter(
                name='categoria',
                description='Filtrar por categoria',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='preco_min',
                description='Preço mínimo',
                required=False,
                type=float
            ),
            OpenApiParameter(
                name='preco_max',
                description='Preço máximo',
                required=False,
                type=float
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Filtros
        categoria = request.query_params.get('categoria')
        preco_min = request.query_params.get('preco_min')
        preco_max = request.query_params.get('preco_max')
        
        if categoria:
            queryset = queryset.filter(categoria__icontains=categoria)
        if preco_min:
            queryset = queryset.filter(preco__gte=preco_min)
        if preco_max:
            queryset = queryset.filter(preco__lte=preco_max)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RAGViewSet(viewsets.ViewSet):
    """
    ViewSet para consultas RAG (Retrieval-Augmented Generation).
    
    Sistema de busca inteligente que usa embeddings e LLM para 
    responder perguntas em linguagem natural sobre o catálogo.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            self.retriever = ProductRetriever()
            self.augmenter = ContextAugmenter()
            self.generator = ResponseGenerator()
        except ImproperlyConfigured as e:
            self.retriever = None
            self.error_message = str(e)
    
    @extend_schema(
        request=RAGQuerySerializer,
        responses={200: RAGResponseSerializer},
        description="Consulta inteligente no catálogo usando linguagem natural",
        examples=[
            OpenApiExample(
                'Exemplo 1',
                summary='Busca por sandália',
                value={'query': 'Quero uma sandália confortável', 'limit': 5}
            ),
            OpenApiExample(
                'Exemplo 2',
                summary='Busca por preço',
                value={'query': 'Tênis até 200 reais', 'limit': 3}
            ),
        ]
    )
    @action(detail=False, methods=['post'])
    def query(self, request):
        """
        Endpoint principal para consultas RAG.
        
        Processa consulta em linguagem natural e retorna:
        - Resposta gerada pelo LLM
        - Produtos mais relevantes
        - Tempo de processamento
        """
        if not self.retriever:
            return Response(
                {'error': self.error_message},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        serializer = RAGQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        query_text = serializer.validated_data['query']
        limit = serializer.validated_data.get('limit', 5)
        
        # Medir tempo de processamento
        start_time = time.time()
        
        try:
            # 1. Buscar produtos relevantes
            produtos = self.retriever.retrieve(query_text, limit=limit)
            
            # 2. Gerar contexto
            contexto = self.augmenter.augment(produtos, query_text)
            
            # 3. Gerar resposta
            resposta = self.generator.generate(query_text, contexto)
            
            tempo_processamento = time.time() - start_time
            
            return Response({
                'query': query_text,
                'resposta': resposta,
                'produtos_encontrados': len(produtos),
                'produtos': produtos,
                'tempo_processamento': round(tempo_processamento, 3)
            })
            
        except Exception as e:
            return Response(
                {'error': f'Erro ao processar consulta: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        description="Busca produtos por similaridade vetorial",
        parameters=[
            OpenApiParameter(name='q', description='Texto da busca', required=True, type=str),
            OpenApiParameter(name='limit', description='Número de resultados', required=False, type=int),
        ]
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Busca vetorial simples (sem geração de resposta).
        
        Retorna apenas os produtos mais similares ao texto da busca.
        """
        if not self.retriever:
            return Response(
                {'error': self.error_message},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        query_text = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 5))
        
        if not query_text:
            return Response(
                {'error': 'Parâmetro "q" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            produtos = self.retriever.retrieve(query_text, limit=limit)
            return Response({
                'query': query_text,
                'total': len(produtos),
                'produtos': produtos
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(description="Estatísticas do catálogo")
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retorna estatísticas gerais do catálogo"""
        if not self.retriever:
            return Response(
                {'error': self.error_message},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            stats = self.retriever.get_statistics()
            return Response(stats)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    description="Endpoint de health check para verificar status da API",
    responses={200: {'description': 'API está funcionando'}}
)
@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'ok',
        'message': 'API RAG funcionando!',
        'version': '1.0.0'
    })