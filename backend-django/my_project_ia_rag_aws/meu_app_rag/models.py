from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Produto(models.Model):
    """Modelo de Produto para o sistema RAG de catálogo"""
    
    # Identificação
    nome = models.CharField(max_length=255)
    
    # Classificação
    categoria = models.CharField(max_length=100)
    subcategoria = models.CharField(max_length=100, blank=True, null=True)
    
    # Precificação
    preco = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    preco_promocional = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    
    # Características
    marca = models.CharField(max_length=100, blank=True, null=True)
    cor = models.CharField(max_length=50, blank=True, null=True)
    tamanho = models.CharField(max_length=50, blank=True, null=True)
    material = models.CharField(max_length=100, blank=True, null=True)
    
    # Estoque
    estoque = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # Descrição
    descricao = models.TextField(blank=True, null=True)
    especificacoes = models.TextField(blank=True, null=True)
    
    # Avaliações
    avaliacao = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    num_avaliacoes = models.IntegerField(default=0)
    
    # Especificações físicas
    peso = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        blank=True,
        null=True,
        help_text="Peso em quilogramas"
    )
    dimensoes = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Formato: LxAxP cm"
    )
    
    # Auditoria
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'produtos'
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['-data_cadastro']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['categoria']),
            models.Index(fields=['preco']),
        ]
    
    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"
    
    def save(self, *args, **kwargs):
        # Validação: preço promocional deve ser menor que preço normal
        if self.preco_promocional and self.preco_promocional >= self.preco:
            raise ValueError('Preço promocional deve ser menor que o preço normal')
        super().save(*args, **kwargs)