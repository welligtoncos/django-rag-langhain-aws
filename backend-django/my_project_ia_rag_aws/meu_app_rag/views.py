import time
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q, Count, Avg
import logging

logger = logging.getLogger(__name__)

from .models import Produto
from .serializers import (
    ProdutoSerializer,
    ProdutoListSerializer,
    ProdutoMinimalSerializer,
    ProdutoImagemSerializer,
    RAGQuerySerializer,
    RAGResponseSerializer
)
from .rag.retriever import ProductRetriever
from .rag.augmenter import ContextAugmenter
from .rag.generator import ResponseGenerator


class StandardResultsSetPagination(PageNumberPagination):
    """Paginação padrão para listagens"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProdutoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operações CRUD de produtos.
    
    Endpoints:
    - GET /api/rag/produtos/ - Lista todos os produtos
    - POST /api/rag/produtos/ - Cria novo produto
    - GET /api/rag/produtos/{id}/ - Detalhe de um produto
    - PUT /api/rag/produtos/{id}/ - Atualiza produto completo
    - PATCH /api/rag/produtos/{id}/ - Atualiza produto parcial
    - DELETE /api/rag/produtos/{id}/ - Remove produto
    - POST /api/rag/produtos/{id}/imagem/ - Upload de imagem
    """
    
    queryset = Produto.objects.all().order_by('-data_cadastro')
    serializer_class = ProdutoSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        """Escolhe serializer baseado na ação"""
        if self.action == 'list':
            return ProdutoListSerializer
        elif self.action == 'imagem':
            return ProdutoImagemSerializer
        return ProdutoSerializer
    
    def get_serializer_context(self):
        """
        Passa request no contexto para construir URLs absolutas de imagens.
        CRÍTICO para imagem_completa e thumbnail_url funcionarem!
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @extend_schema(
        description="Lista produtos com filtros e paginação",
        parameters=[
            OpenApiParameter(
                name='categoria',
                description='Filtrar por categoria (ex: Roupas, Eletrônicos)',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='subcategoria',
                description='Filtrar por subcategoria',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='marca',
                description='Filtrar por marca',
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
            OpenApiParameter(
                name='cor',
                description='Filtrar por cor',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='tamanho',
                description='Filtrar por tamanho',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='em_estoque',
                description='Apenas produtos em estoque (true/false)',
                required=False,
                type=bool
            ),
            OpenApiParameter(
                name='promocao',
                description='Apenas produtos em promoção (true/false)',
                required=False,
                type=bool
            ),
            OpenApiParameter(
                name='search',
                description='Busca por nome ou descrição',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='ordenar',
                description='Ordenação: preco_asc, preco_desc, nome, avaliacao, mais_novo',
                required=False,
                type=str
            ),
            OpenApiParameter(
                name='page',
                description='Número da página',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='page_size',
                description='Itens por página (max: 100)',
                required=False,
                type=int
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Lista produtos com filtros avançados"""
        queryset = self.get_queryset()
        
        # Filtros básicos
        categoria = request.query_params.get('categoria')
        subcategoria = request.query_params.get('subcategoria')
        marca = request.query_params.get('marca')
        cor = request.query_params.get('cor')
        tamanho = request.query_params.get('tamanho')
        
        if categoria:
            queryset = queryset.filter(categoria__icontains=categoria)
        if subcategoria:
            queryset = queryset.filter(subcategoria__icontains=subcategoria)
        if marca:
            queryset = queryset.filter(marca__icontains=marca)
        if cor:
            queryset = queryset.filter(cor__icontains=cor)
        if tamanho:
            queryset = queryset.filter(tamanho__iexact=tamanho)
        
        # Filtros de preço
        preco_min = request.query_params.get('preco_min')
        preco_max = request.query_params.get('preco_max')
        
        if preco_min:
            queryset = queryset.filter(preco__gte=float(preco_min))
        if preco_max:
            queryset = queryset.filter(preco__lte=float(preco_max))
        
        # Filtro de estoque
        em_estoque = request.query_params.get('em_estoque')
        if em_estoque and em_estoque.lower() == 'true':
            queryset = queryset.filter(estoque__gt=0)
        
        # Filtro de promoção
        promocao = request.query_params.get('promocao')
        if promocao and promocao.lower() == 'true':
            queryset = queryset.filter(preco_promocional__isnull=False)
        
        # Busca textual
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) |
                Q(descricao__icontains=search) |
                Q(especificacoes__icontains=search)
            )
        
        # Ordenação
        ordenar = request.query_params.get('ordenar')
        if ordenar:
            ordem_map = {
                'preco_asc': 'preco',
                'preco_desc': '-preco',
                'nome': 'nome',
                'avaliacao': '-avaliacao',
                'mais_novo': '-data_cadastro',
                'mais_vendido': '-num_avaliacoes'
            }
            if ordenar in ordem_map:
                queryset = queryset.order_by(ordem_map[ordenar])
        
        # Paginação
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        request=ProdutoImagemSerializer,
        responses={200: ProdutoImagemSerializer},
        description="Upload ou atualização de imagem do produto"
    )
    @action(detail=True, methods=['post', 'patch'], serializer_class=ProdutoImagemSerializer)
    def imagem(self, request, pk=None):
        """
        Upload ou atualização de imagem.
        
        Aceita:
        - imagem: arquivo (multipart/form-data)
        - imagem_url: URL externa (application/json)
        
        Thumbnail é gerado automaticamente.
        """
        produto = self.get_object()
        serializer = ProdutoImagemSerializer(
            produto,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        description="Estatísticas gerais dos produtos"
    )
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Retorna estatísticas do catálogo de produtos"""
        from django.db.models import Min, Max, Avg
        
        stats = {
            'total_produtos': Produto.objects.count(),
            'produtos_em_estoque': Produto.objects.filter(estoque__gt=0).count(),
            'produtos_em_promocao': Produto.objects.filter(preco_promocional__isnull=False).count(),
            'produtos_com_imagem': Produto.objects.exclude(
                Q(imagem='') & Q(imagem_url__isnull=True)
            ).count(),
            'preco_medio': Produto.objects.aggregate(Avg('preco'))['preco__avg'],
            'preco_min': Produto.objects.aggregate(Min('preco'))['preco__min'],
            'preco_max': Produto.objects.aggregate(Max('preco'))['preco__max'],
            'avaliacao_media': Produto.objects.aggregate(Avg('avaliacao'))['avaliacao__avg'],
            'categorias': list(
                Produto.objects.values('categoria')
                .annotate(total=Count('id'))
                .order_by('-total')
            ),
            'marcas_top': list(
                Produto.objects.values('marca')
                .annotate(total=Count('id'))
                .order_by('-total')[:10]
            )
        }
        
        return Response(stats)


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
                'Busca simples',
                summary='Busca por produto',
                value={'query': 'Quero uma camiseta branca', 'limit': 5}
            ),
            OpenApiExample(
                'Busca por preço',
                summary='Com restrição de preço',
                value={'query': 'Tênis até 200 reais', 'limit': 3}
            ),
            OpenApiExample(
                'Busca específica',
                summary='Com características',
                value={'query': 'Perfume masculino amadeirado', 'limit': 5}
            ),
        ]
    )
    @action(detail=False, methods=['post'])
    def query(self, request):
        """
        Endpoint principal para consultas RAG.
        """
        if not self.retriever:
            return Response(
                {
                    'error': 'Serviço RAG indisponível',
                    'detalhe': self.error_message
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        serializer = RAGQuerySerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Erro de validação: {serializer.errors}")
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        query_text = serializer.validated_data['query']
        limit = serializer.validated_data.get('limit', 5)
        
        logger.info(f"📝 Nova consulta RAG: '{query_text}' (limit={limit})")
        
        # Medir tempo de processamento
        start_time = time.time()
        
        try:
            # 1. Buscar produtos relevantes (retrieval)
            logger.info("🔍 Buscando produtos...")
            produtos = self.retriever.retrieve(query_text, limit=limit)
            logger.info(f"✅ {len(produtos)} produtos encontrados")
            
            # 2. Gerar contexto (augmentation)
            logger.info("📝 Gerando contexto...")
            contexto = self.augmenter.augment(produtos, query_text)
            
            # 3. Gerar resposta (generation)
            logger.info("🤖 Gerando resposta com LLM...")
            resposta = self.generator.generate(query_text, contexto)
            logger.info("✅ Resposta gerada")
            
            tempo_processamento = time.time() - start_time
            
            # Serializar produtos com contexto de request (para URLs de imagens)
            produtos_serializados = ProdutoMinimalSerializer(
                produtos,
                many=True,
                context={'request': request}
            ).data
            
            response_data = {
                'query': query_text,
                'resposta': resposta,
                'produtos_encontrados': len(produtos),
                'produtos': produtos_serializados,
                'tempo_processamento': round(tempo_processamento, 3)
            }
            
            logger.info(f"✅ Consulta processada em {tempo_processamento:.3f}s")
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar consulta: {str(e)}", exc_info=True)
            return Response(
                {
                    'error': 'Erro ao processar consulta',
                    'detalhe': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        description="Busca produtos por similaridade vetorial (sem geração de texto)",
        parameters=[
            OpenApiParameter(
                name='q',
                description='Texto da busca',
                required=True,
                type=str
            ),
            OpenApiParameter(
                name='limit',
                description='Número de resultados (1-20)',
                required=False,
                type=int
            ),
        ]
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Busca vetorial simples (sem geração de resposta).
        
        Retorna apenas os produtos mais similares ao texto da busca.
        Mais rápido que /query/ pois não gera resposta com LLM.
        """
        if not self.retriever:
            return Response(
                {'error': 'Serviço RAG indisponível'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        query_text = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 5))
        
        if not query_text:
            return Response(
                {'error': 'Parâmetro "q" é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if limit < 1 or limit > 20:
            return Response(
                {'error': 'Limit deve estar entre 1 e 20'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_time = time.time()
            produtos = self.retriever.retrieve(query_text, limit=limit)
            tempo_processamento = time.time() - start_time
            
            # Serializar com contexto para URLs de imagens
            produtos_serializados = ProdutoMinimalSerializer(
                produtos,
                many=True,
                context={'request': request}
            ).data
            
            return Response({
                'query': query_text,
                'total': len(produtos),
                'produtos': produtos_serializados,
                'tempo_processamento': round(tempo_processamento, 3)
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(description="Estatísticas do sistema RAG")
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Retorna estatísticas do sistema RAG:
        - Total de produtos
        - Embeddings gerados
        - Dimensão dos vetores
        - Categorias disponíveis
        """
        if not self.retriever:
            return Response(
                {'error': 'Serviço RAG indisponível'},
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
    description="Health check - Verifica se a API está funcionando",
    responses={200: {'description': 'API operacional'}}
)
@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint.
    
    Retorna status da API e serviços conectados.
    """
    from django.db import connection
    
    # Testar conexão com banco
    try:
        connection.ensure_connection()
        db_status = 'ok'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    # Testar serviço RAG
    try:
        retriever = ProductRetriever()
        rag_status = 'ok'
        rag_produtos = retriever.get_statistics().get('total_produtos', 0)
    except Exception as e:
        rag_status = f'error: {str(e)}'
        rag_produtos = 0
    
    return Response({
        'status': 'ok',
        'message': 'API RAG funcionando!',
        'version': '1.0.0',
        'services': {
            'database': db_status,
            'rag': rag_status
        },
        'produtos_catalogados': rag_produtos
    })