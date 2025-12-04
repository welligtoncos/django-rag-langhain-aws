# conhecimento/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.db.models import Q, Count, F
import os
import time

# Imports locais (models e serializers)
from .models import KnowledgeBase, Documento
from .serializers import (
    KnowledgeBaseSerializer,
    DocumentoListSerializer,
    DocumentoDetailSerializer,
    DocumentoCreateSerializer,
    DocumentoUpdateSerializer,
    ChatQuerySerializer,
    ChatResponseSerializer,
    WordUploadSerializer,
    WordUploadResponseSerializer,
    EstatisticasSerializer,
    HealthCheckSerializer
)

# Imports do módulo RAG
from .rag.retriever import MultiBaseRetriever
from .rag.augmenter import ContextAugmenter
from .rag.generator import ResponseGenerator 

# Imports de importadores
from .importers.word_importer import WordImporter


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """ViewSet para Bases de Conhecimento"""
    
    queryset = KnowledgeBase.objects.all()
    serializer_class = KnowledgeBaseSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        """Filtra bases"""
        queryset = super().get_queryset()
        
        # Filtro por tipo
        tipo = self.request.query_params.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        # Filtro por ativo
        ativo = self.request.query_params.get('ativo')
        if ativo is not None:
            ativo_bool = ativo.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(ativo=ativo_bool)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def documentos(self, request, slug=None):
        """Lista documentos de uma base"""
        base = self.get_object()
        documentos = base.documentos.all()
        
        # Filtros
        status_param = request.query_params.get('status')
        if status_param:
            documentos = documentos.filter(status=status_param)
        
        categoria = request.query_params.get('categoria')
        if categoria:
            documentos = documentos.filter(categoria=categoria)
        
        serializer = DocumentoListSerializer(documentos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def ativar(self, request, slug=None):
        """Ativa uma base"""
        base = self.get_object()
        base.ativo = True
        base.save()
        
        serializer = self.get_serializer(base)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def desativar(self, request, slug=None):
        """Desativa uma base"""
        base = self.get_object()
        base.ativo = False
        base.save()
        
        serializer = self.get_serializer(base)
        return Response(serializer.data)


class DocumentoViewSet(viewsets.ModelViewSet):
    """ViewSet para Documentos"""
    
    queryset = Documento.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentoListSerializer
        elif self.action == 'create':
            return DocumentoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentoUpdateSerializer
        return DocumentoDetailSerializer
    
    def get_queryset(self):
        """Filtra documentos"""
        queryset = super().get_queryset()
        
        # Filtro por base
        base_slug = self.request.query_params.get('base')
        if base_slug:
            queryset = queryset.filter(base__slug=base_slug)
        
        # Filtro por status
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filtro por categoria
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        # Filtro: apenas válidos
        apenas_validos = self.request.query_params.get('apenas_validos')
        if apenas_validos == 'true':
            agora = timezone.now()
            queryset = queryset.filter(
                Q(status='ativo'),
                Q(data_inicio__isnull=True) | Q(data_inicio__lte=agora),
                Q(data_fim__isnull=True) | Q(data_fim__gte=agora)
            )
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def historico(self, request, pk=None):
        """Retorna histórico de versões"""
        doc_atual = self.get_object()
        
        # Busca todas versões
        versoes = [doc_atual]
        doc = doc_atual
        
        while doc.documento_anterior:
            doc = doc.documento_anterior
            versoes.append(doc)
        
        versoes.reverse()
        
        serializer = DocumentoListSerializer(versoes, many=True)
        return Response({
            'total_versoes': len(versoes),
            'versao_atual': doc_atual.versao,
            'versoes': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def restaurar_versao(self, request, pk=None):
        """Restaura uma versão anterior"""
        doc_atual = self.get_object()
        versao_desejada = request.data.get('versao')
        
        if not versao_desejada:
            return Response(
                {'error': 'Versão não especificada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Busca versão
        doc = doc_atual
        while doc and doc.versao != int(versao_desejada):
            doc = doc.documento_anterior
        
        if not doc:
            return Response(
                {'error': f'Versão {versao_desejada} não encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Cria nova versão com conteúdo antigo
        manager = KnowledgeManager()
        
        novo_doc = manager.atualizar_documento(
            documento_id=doc_atual.id,
            titulo=doc.titulo,
            conteudo=doc.conteudo,
            categoria=doc.categoria,
            tags=doc.tags
        )
        
        serializer = DocumentoDetailSerializer(novo_doc)
        return Response({
            'message': f'Versão {versao_desejada} restaurada como v{novo_doc.versao}',
            'documento': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def regenerar_embedding(self, request, pk=None):
        """Regenera embedding do documento"""
        doc = self.get_object()
        
        # CORRIGIDO: Import já está no topo do arquivo
        manager = KnowledgeManager()
        manager._gerar_embedding_documento(doc)
        
        # CORRIGIDO: Método correto
        serializer = self.get_serializer(doc)
        return Response({
            'message': 'Embedding regenerado',
            'documento': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def regenerar_todos_embeddings(self, request):
        """Regenera embeddings de todos documentos ativos"""
        base_slug = request.data.get('base_slug')
        
        manager = KnowledgeManager()
        
        if base_slug:
            try:
                base = KnowledgeBase.objects.get(slug=base_slug)
                queryset = Documento.objects.filter(base=base, status='ativo')
            except KnowledgeBase.DoesNotExist:
                return Response(
                    {'error': f'Base {base_slug} não encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            queryset = Documento.objects.filter(status='ativo')
        
        total = queryset.count()
        
        for doc in queryset:
            manager._gerar_embedding_documento(doc)
        
        return Response({
            'message': f'{total} embeddings regenerados',
            'total': total
        })


class ChatViewSet(viewsets.ViewSet):
    """Endpoint principal do chatbot"""
    
    parser_classes = [JSONParser]
    
    @action(detail=False, methods=['post'])
    def query(self, request):
        """
        Consulta RAG completa
        
        POST /api/chat/query/
        Body: {
            "query": "Como faço para batizar?",
            "bases": ["secretaria"],
            "limit": 5,
            "min_score": 0.0,
            "incluir_documentos": true
        }
        """
        # Valida entrada
        serializer = ChatQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        dados = serializer.validated_data
        inicio = time.time()
        
        # 1. Retrieval
        retriever = MultiBaseRetriever()
        documentos = retriever.retrieve(
            query=dados['query'],
            bases=dados.get('bases'),
            limit=dados['limit'],
            min_score=dados['min_score']
        )
        
        if not documentos:
            response_data = {
                'query': dados['query'],
                'resposta': 'Desculpe, não encontrei informações sobre isso no momento. Pode reformular sua pergunta ou entrar em contato com a secretaria.',
                'documentos_encontrados': 0,
                'documentos': [],
                'tempo_processamento': round(time.time() - inicio, 3)
            }
            
            response_serializer = ChatResponseSerializer(response_data)
            return Response(response_serializer.data)
        
        # 2. Augmentation
        augmenter = ContextAugmenter()
        contexto = augmenter.augment(dados['query'], documentos)
        
        # 3. Generation
        generator = ResponseGenerator()
        resposta = generator.generate(contexto, dados['query'])
        
        tempo_total = time.time() - inicio
        
        # Monta resposta
        response_data = {
            'query': dados['query'],
            'resposta': resposta,
            'documentos_encontrados': len(documentos),
            'tempo_processamento': round(tempo_total, 3)
        }
        
        # Inclui documentos se solicitado
        if dados.get('incluir_documentos', True):
            response_data['documentos'] = documentos
        
        response_serializer = ChatResponseSerializer(response_data)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['get'])
    def bases_disponiveis(self, request):
        """Lista bases disponíveis para consulta"""
        bases = KnowledgeBase.objects.filter(ativo=True)
        serializer = KnowledgeBaseSerializer(bases, many=True)
        return Response(serializer.data)


class ImportViewSet(viewsets.ViewSet):
    """Endpoints de importação"""
    
    parser_classes = [MultiPartParser, FormParser]
    
    @action(detail=False, methods=['post'], url_path='upload-word')
    def upload_word(self, request):
        """
        Upload de arquivo Word
        
        POST /api/import/upload-word/
        Body (form-data):
        - file: arquivo .docx
        - base_slug: slug da base
        - categoria: categoria (opcional)
        - tags: tags adicionais (opcional)
        - gerar_embedding: true/false (opcional)
        """
        # Valida entrada
        serializer = WordUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        dados = serializer.validated_data
        arquivo = dados['file']
        
        # Salva temporariamente
        temp_path = default_storage.save(
            f'temp/{arquivo.name}',
            ContentFile(arquivo.read())
        )
        
        temp_full_path = os.path.join(
            default_storage.location,
            temp_path
        )
        
        try:
            # Processa arquivo
            importer = WordImporter()
            documento = importer.processar_word(
                temp_full_path,
                dados['base_slug']
            )
            
            # Sobrescreve categoria/tags se fornecidos
            atualizado = False
            if dados.get('categoria'):
                documento.categoria = dados['categoria']
                atualizado = True
            
            if dados.get('tags'):
                documento.tags.extend(dados['tags'])
                atualizado = True
            
            if atualizado:
                documento.save()
            
            # Remove arquivo temporário
            default_storage.delete(temp_path)
            
            # Monta resposta
            response_data = {
                'success': True,
                'message': 'Documento importado com sucesso!',
                'documento': {
                    'id': documento.id,
                    'titulo': documento.titulo,
                    'categoria': documento.categoria,
                    'tags': documento.tags,
                    'base': documento.base.nome,
                    'status': documento.status,
                    'embedding_gerado': documento.embedding is not None
                }
            }
            
            response_serializer = WordUploadResponseSerializer(response_data)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            # Remove arquivo temporário em caso de erro
            if default_storage.exists(temp_path):
                default_storage.delete(temp_path)
            
            return Response({
                'success': False,
                'error': 'Erro ao processar documento',
                'detalhes': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HealthViewSet(viewsets.ViewSet):
    """Endpoints de monitoramento"""
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """Health check do sistema"""
        
        # Testa database
        try:
            KnowledgeBase.objects.count()
            db_ok = True
        except:
            db_ok = False
        
        # Testa AWS Bedrock
        try:
            from .rag.embeddings import Embeddings
            embeddings = Embeddings()
            embeddings.embed("teste")
            bedrock_ok = True
        except:
            bedrock_ok = False
        
        # Conta embeddings
        embeddings_count = Documento.objects.filter(
            embedding__isnull=False
        ).count()
        
        health_data = {
            'status': 'ok' if (db_ok and bedrock_ok) else 'error',
            'timestamp': timezone.now(),
            'database': db_ok,
            'aws_bedrock': bedrock_ok,
            'embeddings_disponiveis': embeddings_count,
            'versao': '1.0.0'
        }
        
        serializer = HealthCheckSerializer(health_data)
        
        status_code = (
            status.HTTP_200_OK 
            if health_data['status'] == 'ok' 
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
        return Response(serializer.data, status=status_code)
    
    @action(detail=False, methods=['get'])
    def estatisticas(self, request):
        """Estatísticas gerais do sistema"""
        
        # Conta tudo
        total_bases = KnowledgeBase.objects.count()
        bases_ativas = KnowledgeBase.objects.filter(ativo=True).count()
        total_docs = Documento.objects.count()
        docs_ativos = Documento.objects.filter(status='ativo').count()
        
        # Docs por base
        docs_por_base = dict(
            Documento.objects.filter(status='ativo')
            .values('base__nome')
            .annotate(count=Count('id'))
            .values_list('base__nome', 'count')
        )
        
        # Docs por status
        docs_por_status = dict(
            Documento.objects.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        )
        
        # Próximos a expirar (7 dias)
        from datetime import timedelta
        agora = timezone.now()
        proximos_expirar = Documento.objects.filter(
            status='ativo',
            data_fim__isnull=False,
            data_fim__lte=agora + timedelta(days=7),
            data_fim__gte=agora
        ).count()
        
        # Sem embedding
        sem_embedding = Documento.objects.filter(
            status='ativo',
            embedding__isnull=True
        ).count()
        
        stats_data = {
            'total_bases': total_bases,
            'bases_ativas': bases_ativas,
            'total_documentos': total_docs,
            'documentos_ativos': docs_ativos,
            'documentos_por_base': docs_por_base,
            'documentos_por_status': docs_por_status,
            'proximos_a_expirar': proximos_expirar,
            'sem_embedding': sem_embedding
        }
        
        serializer = EstatisticasSerializer(stats_data)
        return Response(serializer.data)
 