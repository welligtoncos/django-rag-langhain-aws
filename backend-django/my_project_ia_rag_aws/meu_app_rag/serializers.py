from rest_framework import serializers
from .models import Produto


class ProdutoSerializer(serializers.ModelSerializer):
    """Serializer completo para operações CRUD"""
    
    class Meta:
        model = Produto
        fields = '__all__'
        read_only_fields = ['data_cadastro', 'data_atualizacao']
    
    def validate(self, data):
        """Validação customizada"""
        if data.get('preco_promocional') and data.get('preco'):
            if data['preco_promocional'] >= data['preco']:
                raise serializers.ValidationError(
                    "Preço promocional deve ser menor que o preço normal"
                )
        return data


class ProdutoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagens"""
    
    class Meta:
        model = Produto
        fields = [
            'id', 'nome', 'categoria', 'preco', 
            'preco_promocional', 'marca', 'estoque', 'avaliacao'
        ]


class RAGQuerySerializer(serializers.Serializer):
    """Serializer para consultas RAG"""
    
    query = serializers.CharField(
        required=True,
        max_length=500,
        help_text="Consulta em linguagem natural"
    )
    limit = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=20,
        help_text="Número máximo de produtos a retornar"
    )


class RAGResponseSerializer(serializers.Serializer):
    """Serializer para respostas do RAG"""
    
    query = serializers.CharField()
    resposta = serializers.CharField()
    produtos_encontrados = serializers.IntegerField()
    produtos = ProdutoListSerializer(many=True)
    tempo_processamento = serializers.FloatField(help_text="Tempo em segundos")