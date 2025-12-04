# conhecimento/admin.py

from datetime import timezone
from django.contrib import admin
from django.utils.html import format_html
from .models import KnowledgeBase, Documento


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ['icone_nome', 'tipo', 'total_docs', 'docs_ativos', 'status_badge']
    list_filter = ['tipo', 'ativo']
    search_fields = ['nome', 'descricao']
    
    def icone_nome(self, obj):
        return format_html(
            '<span style="font-size:18px">{}</span> <strong>{}</strong>',
            obj.icone, obj.nome
        )
    icone_nome.short_description = 'Base'
    
    def total_docs(self, obj):
        return obj.documentos.count()
    total_docs.short_description = 'Total'
    
    def docs_ativos(self, obj):
        count = obj.documentos.filter(status='ativo').count()
        return format_html('<strong style="color:green">{}</strong>', count)
    docs_ativos.short_description = 'Ativos'
    
    def status_badge(self, obj):
        cor = 'green' if obj.ativo else 'red'
        texto = 'Ativa' if obj.ativo else 'Inativa'
        return format_html(
            '<span style="color:{}">{}</span>',
            cor, texto
        )
    status_badge.short_description = 'Status'


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ['base_icon', 'titulo_short', 'categoria', 'status_badge', 'versao', 'validade']
    list_filter = ['base', 'status', 'categoria']
    search_fields = ['titulo', 'conteudo']
    readonly_fields = ['versao', 'documento_anterior', 'embedding_gerado_em']
    
    fieldsets = (
        ('Básico', {
            'fields': ('base', 'titulo', 'slug', 'status')
        }),
        ('Conteúdo', {
            'fields': ('conteudo',),
            'classes': ('wide',)
        }),
        ('Metadados', {
            'fields': ('categoria', 'tags', 'autor')
        }),
        ('Validade', {
            'fields': ('data_inicio', 'data_fim'),
            'classes': ('collapse',)
        }),
        ('Versionamento', {
            'fields': ('versao', 'documento_anterior'),
            'classes': ('collapse',)
        }),
    )
    
    def base_icon(self, obj):
        return format_html(
            '<span style="font-size:18px">{}</span>',
            obj.base.icone
        )
    base_icon.short_description = 'Base'
    
    def titulo_short(self, obj):
        return obj.titulo[:50] + '...' if len(obj.titulo) > 50 else obj.titulo
    titulo_short.short_description = 'Título'
    
    def status_badge(self, obj):
        cores = {
            'ativo': 'green',
            'rascunho': 'orange',
            'arquivado': 'gray',
            'expirado': 'red'
        }
        return format_html(
            '<span style="color:{}">{}</span>',
            cores.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def validade(self, obj):
        if not obj.data_fim:
            return '-'
        
        agora = timezone.now()
        if agora > obj.data_fim:
            return format_html('<span style="color:red">Expirado</span>')
        
        dias = (obj.data_fim - agora).days
        if dias <= 3:
            return format_html('<span style="color:orange">{} dias</span>', dias)
        
        return f'{dias} dias'
    validade.short_description = 'Expira em'