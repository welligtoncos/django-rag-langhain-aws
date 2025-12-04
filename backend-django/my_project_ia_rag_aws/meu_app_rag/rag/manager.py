# conhecimento/rag/manager.py


from django.db import transaction
import uuid

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Q, Count, F

from ..models import Documento, KnowledgeBase
from .embeddings import Embeddings

 
 

logger = logging.getLogger(__name__)


import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Q, Count, F

from ..models import Documento, KnowledgeBase
from .embeddings import Embeddings

logger = logging.getLogger(__name__)


class KnowledgeManager:
    """
    Gerenciador central de bases de conhecimento
    """

    def __init__(self):
        self.embeddings = Embeddings()

    # ====================
    # Helpers (SLUG)
    # ====================

    def _truncate_slug(self, slug: str) -> str:
        field = Documento._meta.get_field("slug")
        max_len = getattr(field, "max_length", None)
        return slug[:max_len] if max_len else slug

    def _make_unique_slug(self, base: KnowledgeBase, base_slug: str) -> str:
        """
        Gera slug único por (base, slug). Se já existir, adiciona sufixo -2, -3, ...
        """
        base_slug = self._truncate_slug(base_slug)
        slug = base_slug
        i = 2
        while Documento.objects.filter(base=base, slug=slug).exists():
            suffix = f"-{i}"
            slug = self._truncate_slug(base_slug[: max(0, len(base_slug) - len(suffix))] + suffix)
            i += 1
        return slug

    def _archive_current_slug(self, doc: Documento) -> str:
        """
        Renomeia o slug do doc atual (arquivado) para liberar o slug original.
        Retorna o slug original para ser usado na nova versão.
        """
        original = doc.slug
        ts = timezone.now().strftime("%Y%m%d%H%M%S")
        new_slug = self._truncate_slug(f"{original}--old--{doc.id}--{ts}")
        doc.slug = new_slug
        doc.save(update_fields=["slug"])
        return original

    # ==================== BASES DE CONHECIMENTO ====================

    def criar_base(
        self,
        nome: str,
        tipo: str,
        descricao: str,
        slug: Optional[str] = None,
        **kwargs
    ) -> KnowledgeBase:
        if not slug:
            slug = slugify(nome)

        if KnowledgeBase.objects.filter(slug=slug).exists():
            raise ValueError(f"Base com slug '{slug}' já existe")

        base = KnowledgeBase.objects.create(
            nome=nome,
            slug=slug,
            tipo=tipo,
            descricao=descricao,
            **kwargs
        )

        logger.info(f"✅ Base criada: {base.nome} ({base.slug})")
        return base

    def listar_bases(self, apenas_ativas: bool = True, tipo: Optional[str] = None) -> List[KnowledgeBase]:
        queryset = KnowledgeBase.objects.all()
        if apenas_ativas:
            queryset = queryset.filter(ativo=True)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return list(queryset.order_by('-prioridade', 'nome'))

    def obter_base(self, slug: str) -> KnowledgeBase:
        return KnowledgeBase.objects.get(slug=slug)

    def ativar_base(self, slug: str) -> KnowledgeBase:
        base = self.obter_base(slug)
        base.ativo = True
        base.save()
        logger.info(f"✅ Base ativada: {base.nome}")
        return base

    def desativar_base(self, slug: str) -> KnowledgeBase:
        base = self.obter_base(slug)
        base.ativo = False
        base.save()
        logger.info(f"🔴 Base desativada: {base.nome}")
        return base

    # ==================== DOCUMENTOS ====================

    def adicionar_documento(
        self,
        base: KnowledgeBase,
        titulo: str,
        conteudo: str,
        categoria: str = "",
        tags: Optional[List[str]] = None,
        autor: str = "",
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        gerar_embedding: bool = True,
        status: str = 'ativo'
    ) -> Documento:

        if not titulo or not titulo.strip():
            raise ValueError("Título não pode ser vazio")

        if not conteudo or len(conteudo.strip()) < 10:
            raise ValueError("Conteúdo muito curto (mínimo 10 caracteres)")

        titulo_limpo = titulo.strip()
        slug_base = slugify(titulo_limpo)
        slug_final = self._make_unique_slug(base, slug_base)

        doc = Documento.objects.create(
            base=base,
            titulo=titulo_limpo,
            slug=slug_final,
            conteudo=conteudo.strip(),
            categoria=categoria.strip() if categoria else "",
            tags=tags or [],
            autor=autor.strip() if autor else "",
            data_inicio=data_inicio,
            data_fim=data_fim,
            status=status,
            versao=1
        )

        logger.info(f"📄 Documento criado: {doc.titulo} (ID: {doc.id})")

        if gerar_embedding:
            try:
                self._gerar_embedding_documento(doc)
            except Exception as e:
                logger.error(f"❌ Erro ao gerar embedding: {e}")

        return doc

    def atualizar_documento(
        self,
        documento_id: int,
        criar_nova_versao: bool = True,
        **campos
    ) -> Documento:

        if criar_nova_versao:
            with transaction.atomic():
                doc_atual = Documento.objects.select_for_update().get(id=documento_id)

                # valida conteúdo novo se foi passado
                if "conteudo" in campos:
                    c = (campos.get("conteudo") or "").strip()
                    if len(c) < 10:
                        raise ValueError("Conteúdo muito curto (mínimo 10 caracteres)")

                # arquiva versão atual
                doc_atual.status = 'arquivado'
                doc_atual.save(update_fields=['status'])

                # libera o slug (renomeia o slug do arquivado)
                slug_original = self._archive_current_slug(doc_atual)

                titulo_novo = (campos.get('titulo', doc_atual.titulo) or "").strip()
                conteudo_novo = (campos.get('conteudo', doc_atual.conteudo) or "").strip()

                novos_campos = {
                    'base': doc_atual.base,
                    'titulo': titulo_novo,
                    'conteudo': conteudo_novo,
                    'categoria': campos.get('categoria', doc_atual.categoria),
                    'tags': campos.get('tags', doc_atual.tags),
                    'autor': campos.get('autor', doc_atual.autor),
                    'data_inicio': campos.get('data_inicio', doc_atual.data_inicio),
                    'data_fim': campos.get('data_fim', doc_atual.data_fim),
                    'versao': doc_atual.versao + 1,
                    'documento_anterior': doc_atual,
                    'status': campos.get('status', 'ativo')
                }

                # se título não mudou, reaproveita slug bonito
                if titulo_novo == doc_atual.titulo:
                    slug_v2 = slug_original
                else:
                    slug_v2 = self._make_unique_slug(doc_atual.base, slugify(titulo_novo))

                novo_doc = Documento.objects.create(
                    slug=slug_v2,
                    **novos_campos
                )

            logger.info(
                f"🔄 Nova versão criada: {novo_doc.titulo} "
                f"(v{novo_doc.versao}, ID: {novo_doc.id})"
            )

            try:
                self._gerar_embedding_documento(novo_doc)
            except Exception as e:
                logger.error(f"❌ Erro ao gerar embedding: {e}")

            return novo_doc

        # --------------------------
        # update in-place (sem versão)
        # --------------------------
        doc_atual = Documento.objects.get(id=documento_id)

        for campo, valor in campos.items():
            if hasattr(doc_atual, campo):
                setattr(doc_atual, campo, valor)

        if 'titulo' in campos:
            titulo_novo = (campos['titulo'] or "").strip()
            doc_atual.slug = self._make_unique_slug(doc_atual.base, slugify(titulo_novo))

        if 'conteudo' in campos:
            c = (campos.get("conteudo") or "").strip()
            if len(c) < 10:
                raise ValueError("Conteúdo muito curto (mínimo 10 caracteres)")

        doc_atual.save()

        if 'conteudo' in campos or 'titulo' in campos:
            try:
                self._gerar_embedding_documento(doc_atual)
            except Exception as e:
                logger.error(f"❌ Erro ao gerar embedding: {e}")

        logger.info(f"✏️ Documento atualizado in-place: {doc_atual.titulo}")
        return doc_atual
    
    def buscar_documentos(
        self,
        base: Optional[KnowledgeBase] = None,
        categoria: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: str = 'ativo',
        apenas_validos: bool = True
    ) -> List[Documento]:
        """
        Busca documentos com filtros
        
        Args:
            base: Filtrar por base específica
            categoria: Filtrar por categoria
            tags: Filtrar por tags (qualquer uma)
            status: Filtrar por status
            apenas_validos: Verificar validade (data_inicio/data_fim)
            
        Returns:
            Lista de documentos
        """
        queryset = Documento.objects.all()
        
        if base:
            queryset = queryset.filter(base=base)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        if tags:
            # Busca documentos com qualquer uma das tags
            queryset = queryset.filter(tags__overlap=tags)
        
        if apenas_validos:
            agora = timezone.now()
            queryset = queryset.filter(
                Q(data_inicio__isnull=True) | Q(data_inicio__lte=agora),
                Q(data_fim__isnull=True) | Q(data_fim__gte=agora)
            )
        
        return list(queryset.order_by('-criado_em'))
    
    def obter_historico_documento(self, documento_id: int) -> List[Documento]:
        """
        Obtém histórico completo de versões de um documento
        
        Args:
            documento_id: ID do documento atual
            
        Returns:
            Lista de versões ordenada (da mais antiga para mais nova)
        """
        doc_atual = Documento.objects.get(id=documento_id)
        
        # Busca todas versões anteriores
        versoes = [doc_atual]
        doc = doc_atual
        
        while doc.documento_anterior:
            doc = doc.documento_anterior
            versoes.append(doc)
        
        # Inverte para ordem cronológica
        versoes.reverse()
        
        return versoes
    
    def restaurar_versao(
        self,
        documento_id: int,
        versao_numero: int
    ) -> Documento:
        """
        Restaura versão anterior de um documento
        
        Cria nova versão com conteúdo da versão especificada
        
        Args:
            documento_id: ID do documento atual
            versao_numero: Número da versão a restaurar
            
        Returns:
            Nova versão criada
        """
        doc_atual = Documento.objects.get(id=documento_id)
        
        # Busca versão desejada
        doc = doc_atual
        while doc and doc.versao != versao_numero:
            doc = doc.documento_anterior
        
        if not doc:
            raise ValueError(f"Versão {versao_numero} não encontrada")
        
        # Cria nova versão com conteúdo da versão antiga
        novo_doc = self.atualizar_documento(
            documento_id=documento_id,
            titulo=doc.titulo,
            conteudo=doc.conteudo,
            categoria=doc.categoria,
            tags=doc.tags
        )
        
        logger.info(
            f"⏪ Versão {versao_numero} restaurada como v{novo_doc.versao}"
        )
        
        return novo_doc
    
    # ==================== EMBEDDINGS ====================
    
    def _gerar_embedding_documento(self, doc: Documento):
        """
        Gera embedding para um documento
        
        Combina título, categoria, tags e conteúdo para criar
        uma representação vetorial rica
        
        Args:
            doc: Documento
        """
        # Monta texto completo para embedding
        partes = []
        
        # Título
        partes.append(f"Título: {doc.titulo}")
        
        # Categoria
        if doc.categoria:
            partes.append(f"Categoria: {doc.categoria}")
        
        # Tags
        if doc.tags:
            partes.append(f"Tags: {', '.join(doc.tags)}")
        
        # Base
        partes.append(f"Base: {doc.base.nome}")
        
        # Conteúdo
        partes.append("")
        partes.append(doc.conteudo)
        
        texto_completo = "\n".join(partes)
        
        # Gera embedding
        logger.debug(f"🔢 Gerando embedding para: {doc.titulo}")
        embedding = self.embeddings.embed(texto_completo)
        
        # Salva no documento
        doc.embedding = embedding.tolist()
        doc.embedding_gerado_em = timezone.now()
        doc.save(update_fields=['embedding', 'embedding_gerado_em'])
        
        logger.debug(f"✅ Embedding gerado: {len(embedding)} dimensões")
    
    def regenerar_embedding(self, documento_id: int):
        """
        Regenera embedding de um documento específico
        
        Args:
            documento_id: ID do documento
        """
        doc = Documento.objects.get(id=documento_id)
        self._gerar_embedding_documento(doc)
        logger.info(f"🔄 Embedding regenerado: {doc.titulo}")
    
    def regenerar_todos_embeddings(
        self,
        base: Optional[KnowledgeBase] = None,
        forcar: bool = False
    ) -> Dict[str, int]:
        """
        Regenera embeddings de múltiplos documentos
        
        Args:
            base: Se fornecida, regenera apenas desta base
            forcar: Se True, regenera mesmo documentos que já têm embedding
            
        Returns:
            Dicionário com estatísticas
        """
        queryset = Documento.objects.filter(status='ativo')
        
        if base:
            queryset = queryset.filter(base=base)
        
        if not forcar:
            # Apenas documentos sem embedding ou desatualizados
            queryset = queryset.filter(
                Q(embedding__isnull=True) |
                Q(embedding_gerado_em__lt=F('atualizado_em'))
            )
        
        total = queryset.count()
        
        if total == 0:
            logger.info("✨ Nenhum documento precisa de embedding")
            return {
                'total': 0,
                'sucesso': 0,
                'erro': 0
            }
        
        logger.info(f"🔄 Regenerando {total} embeddings...")
        
        sucesso = 0
        erro = 0
        
        for i, doc in enumerate(queryset, 1):
            try:
                self._gerar_embedding_documento(doc)
                sucesso += 1
                
                if i % 10 == 0:
                    logger.info(f"   Progresso: {i}/{total}")
            
            except Exception as e:
                logger.error(f"❌ Erro no documento {doc.id}: {e}")
                erro += 1
        
        logger.info(f"✅ Concluído! Sucesso: {sucesso}, Erro: {erro}")
        
        return {
            'total': total,
            'sucesso': sucesso,
            'erro': erro
        }
    
    # ==================== LIFECYCLE (EXPIRAÇÃO) ====================
    
    def expirar_documentos_vencidos(self) -> int:
        """
        Marca como expirado documentos que passaram da data_fim
        
        Returns:
            Número de documentos expirados
        """
        agora = timezone.now()
        
        documentos_vencidos = Documento.objects.filter(
            status='ativo',
            data_fim__lt=agora
        )
        
        total = documentos_vencidos.count()
        
        if total > 0:
            logger.info(f"⏰ Expirando {total} documentos...")
            documentos_vencidos.update(status='expirado')
            logger.info("✅ Documentos expirados!")
        else:
            logger.debug("✨ Nenhum documento para expirar")
        
        return total
    
    def expirar_por_base(self) -> int:
        """
        Expira documentos de bases com auto_expiracao ativada
        
        Returns:
            Número total de documentos expirados
        """
        bases_auto = KnowledgeBase.objects.filter(
            ativo=True,
            auto_expiracao=True
        )
        
        total_expirado = 0
        
        for base in bases_auto:
            if not base.dias_expiracao:
                continue
            
            data_limite = timezone.now() - timedelta(days=base.dias_expiracao)
            
            docs_antigos = Documento.objects.filter(
                base=base,
                status='ativo',
                criado_em__lt=data_limite
            )
            
            count = docs_antigos.count()
            
            if count > 0:
                logger.info(
                    f"⏰ Base '{base.nome}': expirando {count} "
                    f"documentos > {base.dias_expiracao} dias"
                )
                docs_antigos.update(status='expirado')
                total_expirado += count
        
        if total_expirado > 0:
            logger.info(f"✅ Total expirado: {total_expirado}")
        
        return total_expirado
    
    def limpar_documentos_antigos(
        self,
        dias: int = 90,
        apenas_expirados: bool = True
    ) -> int:
        """
        Remove permanentemente documentos antigos
        
        Args:
            dias: Documentos modificados há mais de X dias
            apenas_expirados: Se True, remove apenas expirados
            
        Returns:
            Número de documentos removidos
        """
        data_limite = timezone.now() - timedelta(days=dias)
        
        queryset = Documento.objects.filter(
            atualizado_em__lt=data_limite
        )
        
        if apenas_expirados:
            queryset = queryset.filter(status='expirado')
        
        total = queryset.count()
        
        if total > 0:
            logger.warning(
                f"🗑️  Removendo permanentemente {total} documentos..."
            )
            queryset.delete()
            logger.info("✅ Documentos removidos!")
        
        return total
    
    # ==================== IMPORTAÇÃO EM LOTE ====================
    
    def importar_documentos_json(
        self,
        base: KnowledgeBase,
        arquivo_json: str
    ) -> Dict[str, int]:
        """
        Importa documentos de arquivo JSON
        
        Formato JSON:
        [
            {
                "titulo": "Título do documento",
                "conteudo": "Conteúdo...",
                "categoria": "Categoria",
                "tags": ["tag1", "tag2"],
                "data_inicio": "2025-01-01T00:00:00Z",
                "data_fim": "2025-12-31T23:59:59Z"
            },
            ...
        ]
        
        Args:
            base: Base para importar
            arquivo_json: Caminho do arquivo
            
        Returns:
            Estatísticas da importação
        """
        import json
        from dateutil import parser as date_parser
        
        logger.info(f"📥 Importando de: {arquivo_json}")
        
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        if not isinstance(dados, list):
            raise ValueError("JSON deve conter uma lista de documentos")
        
        total = len(dados)
        sucesso = 0
        erro = 0
        
        logger.info(f"📄 {total} documentos a importar")
        
        for i, item in enumerate(dados, 1):
            try:
                # Parse datas
                data_inicio = None
                data_fim = None
                
                if 'data_inicio' in item:
                    data_inicio = date_parser.parse(item['data_inicio'])
                
                if 'data_fim' in item:
                    data_fim = date_parser.parse(item['data_fim'])
                
                # Cria documento
                self.adicionar_documento(
                    base=base,
                    titulo=item['titulo'],
                    conteudo=item['conteudo'],
                    categoria=item.get('categoria', ''),
                    tags=item.get('tags', []),
                    autor=item.get('autor', ''),
                    data_inicio=data_inicio,
                    data_fim=data_fim
                )
                
                sucesso += 1
                
                if i % 10 == 0:
                    logger.info(f"   Progresso: {i}/{total}")
            
            except Exception as e:
                logger.error(f"❌ Erro no item {i}: {e}")
                erro += 1
        
        logger.info(f"✅ Importação concluída! Sucesso: {sucesso}, Erro: {erro}")
        
        return {
            'total': total,
            'sucesso': sucesso,
            'erro': erro
        }
    
    def importar_documentos_csv(
        self,
        base: KnowledgeBase,
        arquivo_csv: str,
        delimiter: str = ','
    ) -> Dict[str, int]:
        """
        Importa documentos de arquivo CSV
        
        Formato CSV:
        titulo,conteudo,categoria,tags,data_inicio,data_fim
        "Título","Conteúdo...","Categoria","tag1;tag2","2025-01-01",""
        
        Args:
            base: Base para importar
            arquivo_csv: Caminho do arquivo
            delimiter: Delimitador do CSV
            
        Returns:
            Estatísticas da importação
        """
        import csv
        from dateutil import parser as date_parser
        
        logger.info(f"📥 Importando de: {arquivo_csv}")
        
        sucesso = 0
        erro = 0
        
        with open(arquivo_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for i, row in enumerate(reader, 1):
                try:
                    # Parse tags (separadas por ;)
                    tags = []
                    if row.get('tags'):
                        tags = [t.strip() for t in row['tags'].split(';')]
                    
                    # Parse datas
                    data_inicio = None
                    data_fim = None
                    
                    if row.get('data_inicio'):
                        data_inicio = date_parser.parse(row['data_inicio'])
                    
                    if row.get('data_fim'):
                        data_fim = date_parser.parse(row['data_fim'])
                    
                    # Cria documento
                    self.adicionar_documento(
                        base=base,
                        titulo=row['titulo'],
                        conteudo=row['conteudo'],
                        categoria=row.get('categoria', ''),
                        tags=tags,
                        data_inicio=data_inicio,
                        data_fim=data_fim
                    )
                    
                    sucesso += 1
                    
                    if i % 10 == 0:
                        logger.info(f"   Progresso: {i} documentos")
                
                except Exception as e:
                    logger.error(f"❌ Erro na linha {i}: {e}")
                    erro += 1
        
        total = sucesso + erro
        logger.info(f"✅ Importação concluída! Sucesso: {sucesso}, Erro: {erro}")
        
        return {
            'total': total,
            'sucesso': sucesso,
            'erro': erro
        }
    
    # ==================== ESTATÍSTICAS ====================
    
    def obter_estatisticas(self) -> Dict:
        """
        Retorna estatísticas gerais do sistema
        
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            'total_bases': KnowledgeBase.objects.count(),
            'bases_ativas': KnowledgeBase.objects.filter(ativo=True).count(),
            'total_documentos': Documento.objects.count(),
            'documentos_por_status': dict(
                Documento.objects.values('status')
                .annotate(count=Count('id'))
                .values_list('status', 'count')
            ),
            'documentos_por_base': dict(
                Documento.objects.filter(status='ativo')
                .values('base__nome')
                .annotate(count=Count('id'))
                .values_list('base__nome', 'count')
            ),
            'documentos_sem_embedding': Documento.objects.filter(
                status='ativo',
                embedding__isnull=True
            ).count(),
            'proximos_a_expirar': Documento.objects.filter(
                status='ativo',
                data_fim__isnull=False,
                data_fim__lte=timezone.now() + timedelta(days=7)
            ).count()
        }
        
        return stats