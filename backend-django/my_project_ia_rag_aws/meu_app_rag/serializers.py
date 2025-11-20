from rest_framework import serializers
from .models import Produto


class ProdutoSerializer(serializers.ModelSerializer):
    """Serializer completo para operações CRUD"""
    
    # 📸 Campos computados (ANTES do Meta)
    imagem_completa = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    tem_imagem = serializers.SerializerMethodField()
    
    class Meta:
        model = Produto
        fields = [
            # Identificação
            'id', 'nome',
            
            # Classificação
            'categoria', 'subcategoria',
            
            # Precificação
            'preco', 'preco_promocional',
            
            # Características
            'marca', 'cor', 'tamanho', 'material',
            
            # Estoque
            'estoque',
            
            # Descrição
            'descricao', 'especificacoes',
            
            # Avaliações
            'avaliacao', 'num_avaliacoes',
            
            # Especificações físicas
            'peso', 'dimensoes',
            
            # 📸 Imagens
            'imagem', 'imagem_url', 'imagem_thumbnail',
            'imagem_completa', 'thumbnail_url', 'tem_imagem',
            
            # Auditoria
            'data_cadastro', 'data_atualizacao'
        ]
        read_only_fields = [
            'id',
            'data_cadastro',
            'data_atualizacao',
            'imagem_thumbnail',  # Gerado automaticamente
            'imagem_completa',   # Campo computado
            'thumbnail_url',     # Campo computado
            'tem_imagem'         # Campo computado
        ]
    
    def get_imagem_completa(self, obj):
        """Retorna URL completa da imagem principal"""
        request = self.context.get('request')
        
        # Prioridade: imagem local > imagem_url > None
        if obj.imagem:
            if request:
                return request.build_absolute_uri(obj.imagem.url)
            return obj.imagem.url
        elif obj.imagem_url:
            return obj.imagem_url
        
        return None
    
    def get_thumbnail_url(self, obj):
        """Retorna URL do thumbnail (miniatura 200x200)"""
        request = self.context.get('request')
        
        # Se tem thumbnail gerado
        if obj.imagem_thumbnail:
            if request:
                return request.build_absolute_uri(obj.imagem_thumbnail.url)
            return obj.imagem_thumbnail.url
        
        # Fallback: retorna imagem completa
        return self.get_imagem_completa(obj)
    
    def get_tem_imagem(self, obj):
        """Verifica se o produto tem alguma imagem"""
        return obj.tem_imagem()
    
    def validate(self, data):
        """Validações customizadas"""
        # Validação: preço promocional deve ser menor que preço normal
        if data.get('preco_promocional') and data.get('preco'):
            if data['preco_promocional'] >= data['preco']:
                raise serializers.ValidationError({
                    'preco_promocional': 'Preço promocional deve ser menor que o preço normal'
                })
        
        # Validação: pelo menos uma imagem (upload ou URL)
        # Comentado pois imagem é opcional
        # if not data.get('imagem') and not data.get('imagem_url'):
        #     raise serializers.ValidationError({
        #         'imagem': 'É necessário enviar uma imagem ou URL'
        #     })
        
        return data


class ProdutoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagens (menos campos)"""
    
    # 📸 Campos computados
    imagem_completa = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Produto
        fields = [
            'id',
            'nome',
            'categoria',
            'preco',
            'preco_promocional',
            'marca',
            'estoque',
            'avaliacao',
            'imagem',
            'imagem_url',
            'imagem_completa',
            'thumbnail_url'
        ]
    
    def get_imagem_completa(self, obj):
        """Retorna URL completa da imagem"""
        request = self.context.get('request')
        
        if obj.imagem:
            if request:
                return request.build_absolute_uri(obj.imagem.url)
            return obj.imagem.url
        elif obj.imagem_url:
            return obj.imagem_url
        
        return None
    
    def get_thumbnail_url(self, obj):
        """Retorna URL do thumbnail"""
        request = self.context.get('request')
        
        if obj.imagem_thumbnail:
            if request:
                return request.build_absolute_uri(obj.imagem_thumbnail.url)
            return obj.imagem_thumbnail.url
        
        return self.get_imagem_completa(obj)


class ProdutoMinimalSerializer(serializers.Serializer):
    """Serializer minimal para respostas RAG"""
    id = serializers.IntegerField()
    nome = serializers.CharField()
    preco = serializers.DecimalField(max_digits=10, decimal_places=2)
    preco_promocional = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        allow_null=True
    )
    marca = serializers.CharField(required=False, allow_null=True)
    avaliacao = serializers.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        required=False,
        allow_null=True
    )
    estoque = serializers.IntegerField()
    imagem_completa = serializers.SerializerMethodField()
    score = serializers.FloatField(required=False)
    score_percentual = serializers.CharField(required=False)
    
    def get_imagem_completa(self, obj):
        """Retorna URL completa da imagem"""
        request = self.context.get('request')
        
        # Se obj é dict (do retriever)
        if isinstance(obj, dict):
            imagem = obj.get('imagem')
            imagem_url = obj.get('imagem_url')
        else:
            # Se obj é model instance
            imagem = getattr(obj, 'imagem', None)
            imagem_url = getattr(obj, 'imagem_url', None)
        
        # Priorizar imagem_url externa
        if imagem_url:
            return imagem_url
        
        # Se tem imagem local, construir URL completa
        if imagem and request:
            return request.build_absolute_uri(imagem.url if hasattr(imagem, 'url') else imagem)
        
        return None
    
    avaliacao = serializers.FloatField(required=False, allow_null=True)  # ✅ GARANTIR TIPO
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Garantir que avaliacao é float
        if data.get('avaliacao'):
            try:
                data['avaliacao'] = float(data['avaliacao'])
            except (ValueError, TypeError):
                data['avaliacao'] = None
        return data
    
class ProdutoImagemSerializer(serializers.ModelSerializer):
    """Serializer específico para upload/atualização de imagens"""
    
    imagem_completa = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Produto
        fields = [
            'id',
            'nome',
            'imagem',
            'imagem_url',
            'imagem_thumbnail',
            'imagem_completa',
            'thumbnail_url'
        ]
        read_only_fields = [
            'id',
            'nome',
            'imagem_thumbnail',
            'imagem_completa',
            'thumbnail_url'
        ]
    
    def get_imagem_completa(self, obj):
        """Retorna URL completa da imagem"""
        request = self.context.get('request')
        
        if obj.imagem:
            if request:
                return request.build_absolute_uri(obj.imagem.url)
            return obj.imagem.url
        elif obj.imagem_url:
            return obj.imagem_url
        
        return None
    
    def get_thumbnail_url(self, obj):
        """Retorna URL do thumbnail"""
        request = self.context.get('request')
        
        if obj.imagem_thumbnail:
            if request:
                return request.build_absolute_uri(obj.imagem_thumbnail.url)
            return obj.imagem_thumbnail.url
        
        return self.get_imagem_completa(obj)


class RAGQuerySerializer(serializers.Serializer):
    """Serializer para consultas RAG"""
    
    query = serializers.CharField(
        required=True,
        max_length=500,
        help_text="Consulta em linguagem natural (ex: 'camiseta branca barata')"
    )
    limit = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=20,
        help_text="Número máximo de produtos a retornar (1-20)"
    )


class RAGResponseSerializer(serializers.Serializer):
    """Serializer para respostas do RAG"""
    
    query = serializers.CharField(
        help_text="Query original do usuário"
    )
    resposta = serializers.CharField(
        help_text="Resposta gerada pela IA"
    )
    produtos_encontrados = serializers.IntegerField(
        help_text="Quantidade de produtos encontrados"
    )
    produtos = ProdutoMinimalSerializer(
        many=True,
        help_text="Lista de produtos relevantes"
    )
    tempo_processamento = serializers.FloatField(
        help_text="Tempo de processamento em segundos"
    )