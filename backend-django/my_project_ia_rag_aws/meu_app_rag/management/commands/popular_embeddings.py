import os
import pickle
import numpy as np
from unidecode import unidecode
from django.core.management.base import BaseCommand
from django.db import connection

from meu_app_rag.models import Produto
from meu_app_rag.rag.embeddings import Embeddings
from config.settings_rag import CATALOGO_PKL, VECTORS_PKL, DATA_DIR


class Command(BaseCommand):
    help = 'Gera embeddings para todos os produtos do catálogo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força regeneração mesmo se arquivos existirem',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        
        self.stdout.write(self.style.SUCCESS('\n=== GERADOR DE EMBEDDINGS RAG ===\n'))
        
        # Criar diretório se não existir
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Verificar se arquivos já existem
        if os.path.exists(CATALOGO_PKL) and os.path.exists(VECTORS_PKL) and not force:
            self.stdout.write(
                self.style.WARNING(
                    'Arquivos já existem. Use --force para regenerar.'
                )
            )
            return
        
        # 1. Exportar catálogo
        self.stdout.write('\n📦 Exportando catálogo...')
        self.exportar_catalogo()
        
        # 2. Gerar embeddings
        self.stdout.write('\n🧠 Gerando embeddings...')
        self.gerar_embeddings()
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n✅ Processo concluído!\n'
                'Arquivos gerados:\n'
                f'  - {CATALOGO_PKL}\n'
                f'  - {VECTORS_PKL}\n'
            )
        )

    def exportar_catalogo(self):
        """Exporta produtos do banco para arquivo pickle"""
        produtos = Produto.objects.all()
        
        if not produtos.exists():
            self.stdout.write(
                self.style.WARNING(
                    '⚠️ Nenhum produto encontrado no banco!\n'
                    'Execute: python manage.py migrate\n'
                    'E adicione produtos via admin ou API.'
                )
            )
            catalogo = {}
        else:
            catalogo = {}
            for p in produtos:
                catalogo[p.id] = {
                    'id': p.id,
                    'nome': p.nome,
                    'categoria': p.categoria,
                    'subcategoria': p.subcategoria,
                    'preco': float(p.preco) if p.preco else 0,
                    'preco_promocional': float(p.preco_promocional) if p.preco_promocional else None,
                    'marca': p.marca,
                    'cor': p.cor,
                    'tamanho': p.tamanho,
                    'material': p.material,
                    'estoque': p.estoque,
                    'descricao': p.descricao,
                    'especificacoes': p.especificacoes,
                    'avaliacao': float(p.avaliacao) if p.avaliacao else None,
                    'num_avaliacoes': p.num_avaliacoes,
                    'peso': float(p.peso) if p.peso else None,
                    'dimensoes': p.dimensoes,
                }
        
        with open(CATALOGO_PKL, 'wb') as f:
            pickle.dump(catalogo, f)
        
        self.stdout.write(
            self.style.SUCCESS(f'✔ {len(catalogo)} produtos exportados')
        )

    def gerar_embeddings(self):
        """Gera embeddings para todos os produtos"""
        # Carregar catálogo
        with open(CATALOGO_PKL, 'rb') as f:
            catalogo = pickle.load(f)
        
        if not catalogo:
            self.stdout.write(
                self.style.WARNING('⚠️ Catálogo vazio, nenhum embedding gerado.')
            )
            # Salvar arquivo vazio para evitar erro no retriever
            with open(VECTORS_PKL, 'wb') as f:
                pickle.dump({'ids': [], 'vectors': []}, f)
            return
        
        emb = Embeddings()
        
        ids = []
        vectors = []
        
        total = len(catalogo)
        for idx, (pid, produto) in enumerate(catalogo.items(), 1):
            # Criar texto descritivo para embedding
            texto_partes = [
                produto.get('nome', ''),
                produto.get('descricao', ''),
                f"Categoria: {produto.get('categoria', '')}",
                f"Marca: {produto.get('marca', '')}" if produto.get('marca') else '',
            ]
            
            texto = '. '.join(filter(None, texto_partes))
            texto_norm = unidecode(texto.lower())
            
            try:
                vetor = emb.embed(texto_norm)
                ids.append(pid)
                vectors.append(vetor)
                
                self.stdout.write(
                    f'  [{idx}/{total}] ✔ Embedding gerado para ID={pid}: {produto.get("nome", "")[:50]}'
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✖ Erro ao gerar embedding para ID={pid}: {e}')
                )
        
        # Salvar vetores
        with open(VECTORS_PKL, 'wb') as f:
            pickle.dump({
                'ids': ids,
                'vectors': np.array(vectors)
            }, f)
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✔ {len(vectors)} embeddings salvos')
        )