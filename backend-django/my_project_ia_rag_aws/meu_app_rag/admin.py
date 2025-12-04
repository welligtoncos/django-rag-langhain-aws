# conhecimento/admin.py

from django.utils import timezone
from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.urls import path
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


class DocumentoForm(forms.ModelForm):
    tags_input = forms.CharField(
        label='Tags',
        required=False,
        help_text='Separe as tags por vírgula (ex: missa, saude, sexta)',
        widget=forms.TextInput(attrs={'class': 'vTextField'})
    )

    class Meta:
        model = Documento
        fields = '__all__'
        exclude = ['tags']  # Esconde o campo JSON original

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.tags:
            # Converte lista JSON para string separada por vírgula
            self.fields['tags_input'].initial = ', '.join(self.instance.tags)

    def clean_tags_input(self):
        data = self.cleaned_data['tags_input']
        if not data:
            return []
        # Converte string de volta para lista
        return [tag.strip() for tag in data.split(',') if tag.strip()]

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tags = self.cleaned_data['tags_input']
        if commit:
            instance.save()
        return instance


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    form = DocumentoForm
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
            'fields': ('categoria', 'tags_input', 'autor')
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

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('upload-word/', self.admin_site.admin_view(self.upload_word_view), name='documento_upload_word'),
        ]
        return my_urls + urls

    def upload_word_view(self, request):
        from django.shortcuts import render, redirect
        from django.contrib import messages
        from ..models import KnowledgeBase
        from ..importers.word_importer import WordImporter
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        import os

        if request.method == 'POST':
            file = request.FILES.get('file')
            base_slug = request.POST.get('base_slug')

            if not file or not base_slug:
                messages.error(request, 'Por favor, selecione um arquivo e uma base.')
                return redirect('.')

            # Salva temporariamente
            temp_path = default_storage.save(
                f'temp/{file.name}',
                ContentFile(file.read())
            )
            temp_full_path = os.path.join(default_storage.location, temp_path)

            try:
                importer = WordImporter()
                doc = importer.processar_word(temp_full_path, base_slug)
                messages.success(request, f'Documento "{doc.titulo}" importado com sucesso!')
                return redirect('admin:meu_app_rag_documento_changelist')
            except Exception as e:
                messages.error(request, f'Erro ao importar: {str(e)}')
            finally:
                if default_storage.exists(temp_path):
                    default_storage.delete(temp_path)

        bases = KnowledgeBase.objects.filter(ativo=True)
        context = dict(
            self.admin_site.each_context(request),
            bases=bases,
            title='Importar Word'
        )
        return render(request, 'admin/meu_app_rag/documento/upload_word.html', context)