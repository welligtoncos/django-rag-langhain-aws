from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver
from PIL import Image  # ✅ Import necessário para thumbnail
import os
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile


def validate_image_size(image):
    """Valida tamanho máximo da imagem (5MB)"""
    max_size = 5 * 1024 * 1024  # 5MB
    if image.size > max_size:
        raise ValidationError('Imagem muito grande. Tamanho máximo: 5MB')


class Produto(models.Model):
    """Modelo de Produto para o sistema RAG de catálogo"""
    
    # ============================================
    # IDENTIFICAÇÃO
    # ============================================
    nome = models.CharField(max_length=255)
    
    # ============================================
    # 📸 CAMPOS DE IMAGEM
    # ============================================
    imagem = models.ImageField(
        upload_to='produtos/%Y/%m/',
        blank=True,
        null=True,
        help_text="Imagem do produto (JPG, PNG, WebP) - Máx: 5MB",
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
            validate_image_size
        ]
    )
    imagem_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL da imagem (alternativa ao upload)"
    )
    imagem_thumbnail = models.ImageField(
        upload_to='produtos/%Y/%m/thumbnails/',
        blank=True,
        null=True,
        editable=False,
        help_text="Miniatura gerada automaticamente (200x200)"
    )
    
    # ============================================
    # CLASSIFICAÇÃO
    # ============================================
    categoria = models.CharField(max_length=100)
    subcategoria = models.CharField(max_length=100, blank=True, null=True)
    
    # ============================================
    # PRECIFICAÇÃO
    # ============================================
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
    
    # ============================================
    # CARACTERÍSTICAS
    # ============================================
    marca = models.CharField(max_length=100, blank=True, null=True)
    cor = models.CharField(max_length=50, blank=True, null=True)
    tamanho = models.CharField(max_length=50, blank=True, null=True)
    material = models.CharField(max_length=100, blank=True, null=True)
    
    # ============================================
    # ESTOQUE
    # ============================================
    estoque = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    # ============================================
    # DESCRIÇÃO
    # ============================================
    descricao = models.TextField(blank=True, null=True)
    especificacoes = models.TextField(blank=True, null=True)
    
    # ============================================
    # AVALIAÇÕES
    # ============================================
    avaliacao = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    num_avaliacoes = models.IntegerField(default=0)
    
    # ============================================
    # ESPECIFICAÇÕES FÍSICAS
    # ============================================
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
    
    # ============================================
    # AUDITORIA
    # ============================================
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    # ============================================
    # META
    # ============================================
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
    
    # ============================================
    # MÉTODOS ESPECIAIS
    # ============================================
    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"
    
    def save(self, *args, **kwargs):
        """Validações e processamento antes de salvar"""
        # Validação: preço promocional deve ser menor que preço normal
        if self.preco_promocional and self.preco_promocional >= self.preco:
            raise ValueError('Preço promocional deve ser menor que o preço normal')
        
        # Salvar primeiro para ter o arquivo disponível
        super().save(*args, **kwargs)
        
        # Gerar thumbnail se houver imagem e ainda não tiver thumbnail
        if self.imagem and not self.imagem_thumbnail:
            self.criar_thumbnail()
            # Salvar novamente apenas o campo thumbnail
            super().save(update_fields=['imagem_thumbnail'])
    
    def delete(self, *args, **kwargs):
        """Deleta arquivos de imagem ao deletar produto"""
        # Deletar imagem principal
        if self.imagem:
            if os.path.isfile(self.imagem.path):
                os.remove(self.imagem.path)
        
        # Deletar thumbnail
        if self.imagem_thumbnail:
            if os.path.isfile(self.imagem_thumbnail.path):
                os.remove(self.imagem_thumbnail.path)
        
        super().delete(*args, **kwargs)
    
    # ============================================
    # MÉTODOS AUXILIARES
    # ============================================
    def get_imagem_url(self):
        """Retorna a URL da imagem (upload ou externa)"""
        if self.imagem:
            return self.imagem.url
        elif self.imagem_url:
            return self.imagem_url
        return None
    
    def get_thumbnail_url(self):
        """Retorna a URL do thumbnail"""
        if self.imagem_thumbnail:
            return self.imagem_thumbnail.url
        return self.get_imagem_url()  # Fallback para imagem original
    
    def tem_imagem(self):
        """Verifica se o produto tem imagem"""
        return bool(self.imagem or self.imagem_url)
    
    def criar_thumbnail(self):
        """Cria thumbnail da imagem (200x200)"""
        if not self.imagem:
            return
        
        try:
            # Abrir imagem original
            img = Image.open(self.imagem.path)
            
            # Converter para RGB se necessário (para PNG com transparência)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionar mantendo aspect ratio
            img.thumbnail((200, 200), Image.Lanczos)
            
            # Salvar em BytesIO
            thumb_io = BytesIO()
            img.save(thumb_io, format='JPEG', quality=85)
            thumb_io.seek(0)
            
            # Nome do arquivo thumbnail
            thumb_name = f"thumb_{os.path.basename(self.imagem.name)}"
            
            # Salvar no campo imagem_thumbnail
            self.imagem_thumbnail.save(
                thumb_name,
                InMemoryUploadedFile(
                    thumb_io,
                    None,
                    thumb_name,
                    'image/jpeg',
                    thumb_io.getbuffer().nbytes,
                    None
                ),
                save=False
            )
        except Exception as e:
            # Log do erro (opcional)
            print(f"Erro ao criar thumbnail: {e}")


# ============================================
# SIGNALS
# ============================================
@receiver(pre_save, sender=Produto)
def delete_old_image(sender, instance, **kwargs):
    """Deleta imagem e thumbnail antigos quando uma nova é enviada"""
    if not instance.pk:
        return False
    
    try:
        old_produto = Produto.objects.get(pk=instance.pk)
    except Produto.DoesNotExist:
        return False
    
    # Deletar imagem antiga se mudou
    if old_produto.imagem and old_produto.imagem != instance.imagem:
        if os.path.isfile(old_produto.imagem.path):
            os.remove(old_produto.imagem.path)
    
    # Deletar thumbnail antigo se mudou a imagem
    if old_produto.imagem_thumbnail and old_produto.imagem != instance.imagem:
        if os.path.isfile(old_produto.imagem_thumbnail.path):
            os.remove(old_produto.imagem_thumbnail.path)
        # Limpar campo thumbnail para que seja recriado
        instance.imagem_thumbnail = None