# meu_app_rag/admin.py

from django.contrib import admin
from .models import Produto

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'categoria', 'preco', 'estoque', 'tem_imagem']
    list_filter = ['categoria', 'marca']
    search_fields = ['nome', 'descricao']
    
    # 📸 Mostrar miniatura da imagem
    readonly_fields = ['preview_imagem']
    
    def preview_imagem(self, obj):
        if obj.get_imagem_url():
            return f'<img src="{obj.get_imagem_url()}" width="200" />'
        return "Sem imagem"
    preview_imagem.allow_tags = True
    preview_imagem.short_description = "Preview"