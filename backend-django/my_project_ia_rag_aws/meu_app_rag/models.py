# conhecimento/models.py

from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Q


class KnowledgeBase(models.Model):
    """Base de conhecimento (Collection)"""
    
    TIPO_CHOICES = [
        ('temporario', 'Temporário'),
        ('atualizavel', 'Atualizável'),
        ('estatico', 'Estático'),
    ]
    
    nome = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    descricao = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    ativo = models.BooleanField(default=True)
    prioridade = models.IntegerField(default=0)
    cor = models.CharField(max_length=7, default='#3B82F6')
    icone = models.CharField(max_length=50, default='📚')
    
    auto_expiracao = models.BooleanField(default=False)
    dias_expiracao = models.IntegerField(null=True, blank=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Base de Conhecimento'
        verbose_name_plural = 'Bases de Conhecimento'
        ordering = ['-prioridade', 'nome']
    
    def __str__(self):
        return f"{self.icone} {self.nome}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)


class Documento(models.Model):
    """Documento/Artigo em uma base"""
    
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('ativo', 'Ativo'),
        ('arquivado', 'Arquivado'),
        ('expirado', 'Expirado'),
    ]
    
    base = models.ForeignKey(
        KnowledgeBase,
        on_delete=models.CASCADE,
        related_name='documentos'
    )
    
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(blank=True)
    conteudo = models.TextField()
    
    categoria = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list)
    autor = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ativo'
    )
    
    data_inicio = models.DateTimeField(null=True, blank=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    
    versao = models.IntegerField(default=1)
    documento_anterior = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='versoes'
    )
    
    embedding = models.JSONField(null=True, blank=True)
    embedding_gerado_em = models.DateTimeField(null=True, blank=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'
        ordering = ['-criado_em']
        unique_together = [['base', 'slug']]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['base', 'status']),
            models.Index(fields=['data_fim']),
        ]
    
    def __str__(self):
        return f"[{self.base.nome}] {self.titulo}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)
    
    def is_valido(self):
        """Verifica se documento está válido"""
        if self.status != 'ativo':
            return False
        
        agora = timezone.now()
        
        if self.data_inicio and agora < self.data_inicio:
            return False
        
        if self.data_fim and agora > self.data_fim:
            return False
        
        return True
    
    def expirar(self):
        """Marca como expirado"""
        self.status = 'expirado'
        self.save()