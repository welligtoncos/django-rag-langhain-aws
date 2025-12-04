# conhecimento/serializers.py

from rest_framework import serializers
from .models import KnowledgeBase, Documento
from django.utils import timezone


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    """Serializer para Base de Conhecimento"""
    
    total_documentos = serializers.SerializerMethodField()
    documentos_ativos = serializers.SerializerMethodField()
    
    class Meta:
        model = KnowledgeBase
        fields = [
            'id',
            'nome',
            'slug',
            'descricao',
            'tipo',
            'ativo',
            'prioridade',
            'cor',
            'icone',
            'auto_expiracao',
            'dias_expiracao',
            'total_documentos',
            'documentos_ativos',
            'criado_em',
            'atualizado_em'
        ]
        read_only_fields = ['id', 'criado_em', 'atualizado_em']
    
    def get_total_documentos(self, obj):
        return obj.documentos.count()
    
    def get_documentos_ativos(self, obj):
        return obj.documentos.filter(status='ativo').count()


class KnowledgeBaseSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado (para nested objects)"""
    
    class Meta:
        model = KnowledgeBase
        fields = ['id', 'nome', 'slug', 'icone', 'tipo', 'cor']


class DocumentoListSerializer(serializers.ModelSerializer):
    """Serializer para listagem de documentos"""
    
    base = KnowledgeBaseSimpleSerializer(read_only=True)
    is_valido = serializers.SerializerMethodField()
    dias_para_expirar = serializers.SerializerMethodField()
    tem_embedding = serializers.SerializerMethodField()
    
    class Meta:
        model = Documento
        fields = [
            'id',
            'base',
            'titulo',
            'slug',
            'categoria',
            'tags',
            'status',
            'versao',
            'data_inicio',
            'data_fim',
            'is_valido',
            'dias_para_expirar',
            'tem_embedding',
            'criado_em',
            'atualizado_em'
        ]
    
    def get_is_valido(self, obj):
        return obj.is_valido()
    
    def get_dias_para_expirar(self, obj):
        if not obj.data_fim:
            return None
        
        agora = timezone.now()
        if agora > obj.data_fim:
            return 0
        
        delta = obj.data_fim - agora
        return delta.days
    
    def get_tem_embedding(self, obj):
        return obj.embedding is not None


class DocumentoDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado de documento"""
    
    base = KnowledgeBaseSimpleSerializer(read_only=True)
    documento_anterior = serializers.SerializerMethodField()
    versoes_posteriores = serializers.SerializerMethodField()
    is_valido = serializers.SerializerMethodField()
    tem_embedding = serializers.SerializerMethodField()
    
    class Meta:
        model = Documento
        fields = [
            'id',
            'base',
            'titulo',
            'slug',
            'conteudo',
            'categoria',
            'tags',
            'autor',
            'status',
            'versao',
            'documento_anterior',
            'versoes_posteriores',
            'data_inicio',
            'data_fim',
            'is_valido',
            'tem_embedding',
            'embedding_gerado_em',
            'criado_em',
            'atualizado_em'
        ]
    
    def get_documento_anterior(self, obj):
        if obj.documento_anterior:
            return {
                'id': obj.documento_anterior.id,
                'titulo': obj.documento_anterior.titulo,
                'versao': obj.documento_anterior.versao,
                'criado_em': obj.documento_anterior.criado_em
            }
        return None
    
    def get_versoes_posteriores(self, obj):
        versoes = Documento.objects.filter(documento_anterior=obj)
        return [{
            'id': v.id,
            'titulo': v.titulo,
            'versao': v.versao,
            'status': v.status,
            'criado_em': v.criado_em
        } for v in versoes]
    
    def get_is_valido(self, obj):
        return obj.is_valido()
    
    def get_tem_embedding(self, obj):
        return obj.embedding is not None


class DocumentoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criar documento"""
    
    base_slug = serializers.SlugField(write_only=True)
    gerar_embedding = serializers.BooleanField(default=True, write_only=True)
    
    class Meta:
        model = Documento
        fields = [
            'base_slug',
            'titulo',
            'conteudo',
            'categoria',
            'tags',
            'autor',
            'data_inicio',
            'data_fim',
            'gerar_embedding'
        ]
    
    def validate_base_slug(self, value):
        """Valida se base existe e está ativa"""
        try:
            base = KnowledgeBase.objects.get(slug=value, ativo=True)
            return base
        except KnowledgeBase.DoesNotExist:
            raise serializers.ValidationError(
                f"Base '{value}' não encontrada ou inativa"
            )
    
    def validate_conteudo(self, value):
        """Valida tamanho do conteúdo"""
        if len(value.strip()) < 50:
            raise serializers.ValidationError(
                "Conteúdo muito curto (mínimo 50 caracteres)"
            )
        return value
    
    def validate(self, data):
        """Validações gerais"""
        # Valida datas
        if data.get('data_inicio') and data.get('data_fim'):
            if data['data_inicio'] >= data['data_fim']:
                raise serializers.ValidationError({
                    'data_fim': 'data_fim deve ser posterior a data_inicio'
                })
        
        return data
    
    def create(self, validated_data):
        """Cria documento e gera embedding"""
        from .rag.manager import KnowledgeManager
        
        base = validated_data.pop('base_slug')
        gerar_embedding = validated_data.pop('gerar_embedding', True)
        
        manager = KnowledgeManager()
        documento = manager.adicionar_documento(
            base=base,
            titulo=validated_data['titulo'],
            conteudo=validated_data['conteudo'],
            categoria=validated_data.get('categoria', ''),
            tags=validated_data.get('tags', []),
            data_inicio=validated_data.get('data_inicio'),
            data_fim=validated_data.get('data_fim'),
            gerar_embedding=gerar_embedding
        )
        
        return documento


class DocumentoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualizar documento (cria nova versão)"""
    
    class Meta:
        model = Documento
        fields = [
            'titulo',
            'conteudo',
            'categoria',
            'tags',
            'data_inicio',
            'data_fim'
        ]
    
    def update(self, instance, validated_data):
        """Atualiza documento criando nova versão"""
        from .rag.manager import KnowledgeManager
        
        manager = KnowledgeManager()
        novo_documento = manager.atualizar_documento(
            documento_id=instance.id,
            **validated_data
        )
        
        return novo_documento


class DocumentoSearchResultSerializer(serializers.Serializer):
    """Serializer para resultado de busca (não é um model)"""
    
    id = serializers.IntegerField()
    titulo = serializers.CharField()
    conteudo = serializers.CharField()
    categoria = serializers.CharField(allow_blank=True)
    tags = serializers.ListField(child=serializers.CharField())
    base = serializers.DictField()
    score = serializers.FloatField()
    data_fim = serializers.DateTimeField(allow_null=True)
    criado_em = serializers.DateTimeField()


class ChatQuerySerializer(serializers.Serializer):
    """Serializer para consulta do chat"""
    
    query = serializers.CharField(
        required=True,
        min_length=3,
        max_length=500,
        error_messages={
            'required': 'Campo query é obrigatório',
            'min_length': 'Query deve ter no mínimo 3 caracteres',
            'max_length': 'Query deve ter no máximo 500 caracteres'
        }
    )
    
    bases = serializers.ListField(
        child=serializers.SlugField(),
        required=False,
        allow_empty=True,
        help_text='Lista de slugs de bases para buscar (opcional)'
    )
    
    limit = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=20,
        help_text='Número máximo de documentos a retornar'
    )
    
    min_score = serializers.FloatField(
        default=0.0,
        min_value=0.0,
        max_value=1.0,
        help_text='Score mínimo de relevância (0.0 a 1.0)'
    )
    
    incluir_documentos = serializers.BooleanField(
        default=True,
        help_text='Incluir documentos encontrados na resposta'
    )
    
    def validate_bases(self, value):
        """Valida se as bases existem"""
        if value:
            bases_existentes = KnowledgeBase.objects.filter(
                slug__in=value,
                ativo=True
            ).values_list('slug', flat=True)
            
            bases_invalidas = set(value) - set(bases_existentes)
            
            if bases_invalidas:
                raise serializers.ValidationError(
                    f"Bases não encontradas ou inativas: {', '.join(bases_invalidas)}"
                )
        
        return value


class ChatResponseSerializer(serializers.Serializer):
    """Serializer para resposta do chat"""
    
    query = serializers.CharField()
    resposta = serializers.CharField()
    documentos_encontrados = serializers.IntegerField()
    documentos = DocumentoSearchResultSerializer(many=True, required=False)
    tempo_processamento = serializers.FloatField()
    metadata = serializers.DictField(required=False)


class WordUploadSerializer(serializers.Serializer):
    """Serializer para upload de Word"""
    
    file = serializers.FileField(
        required=True,
        help_text='Arquivo .docx a ser importado'
    )
    
    base_slug = serializers.SlugField(
        required=True,
        help_text='Slug da base de conhecimento'
    )
    
    categoria = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
        help_text='Categoria do documento (opcional, sobrescreve do arquivo)'
    )
    
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        help_text='Tags adicionais (opcional, complementa do arquivo)'
    )
    
    gerar_embedding = serializers.BooleanField(
        default=True,
        help_text='Gerar embedding automaticamente'
    )
    
    def validate_file(self, value):
        """Valida arquivo"""
        # Valida extensão
        if not value.name.endswith('.docx'):
            raise serializers.ValidationError(
                'Apenas arquivos .docx são aceitos'
            )
        
        # Valida tamanho (10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                'Arquivo muito grande. Máximo: 10MB'
            )
        
        return value
    
    def validate_base_slug(self, value):
        """Valida se base existe"""
        try:
            KnowledgeBase.objects.get(slug=value, ativo=True)
            return value
        except KnowledgeBase.DoesNotExist:
            raise serializers.ValidationError(
                f"Base '{value}' não encontrada ou inativa"
            )


class WordUploadResponseSerializer(serializers.Serializer):
    """Serializer para resposta de upload"""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    avisos = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    documento = serializers.DictField()


class EstatisticasSerializer(serializers.Serializer):
    """Serializer para estatísticas gerais"""
    
    total_bases = serializers.IntegerField()
    bases_ativas = serializers.IntegerField()
    total_documentos = serializers.IntegerField()
    documentos_ativos = serializers.IntegerField()
    documentos_por_base = serializers.DictField()
    documentos_por_status = serializers.DictField()
    proximos_a_expirar = serializers.IntegerField()
    sem_embedding = serializers.IntegerField()


class HealthCheckSerializer(serializers.Serializer):
    """Serializer para health check"""
    
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    database = serializers.BooleanField()
    aws_bedrock = serializers.BooleanField()
    embeddings_disponiveis = serializers.IntegerField()
    versao = serializers.CharField()