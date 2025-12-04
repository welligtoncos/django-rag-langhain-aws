# conhecimento/management/commands/criar_bases.py

from django.core.management.base import BaseCommand

from ...models import KnowledgeBase



class Command(BaseCommand):
    help = 'Cria bases de conhecimento padrão'
    
    def handle(self, *args, **options):
        bases = [
            {
                'nome': 'Secretaria Paroquial',
                'slug': 'secretaria',
                'tipo': 'atualizavel',
                'descricao': 'Serviços e sacramentos',
                'icone': '🏛️',
                'prioridade': 90,
                'cor': '#8B4513'
            },
            {
                'nome': 'Informações da Paróquia',
                'slug': 'paroquia',
                'tipo': 'estatico',
                'descricao': 'Horários, localização, contatos',
                'icone': '⛪',
                'prioridade': 80,
                'cor': '#4169E1'
            },
            {
                'nome': 'Avisos da Semana',
                'slug': 'avisos-semanais',
                'tipo': 'temporario',
                'descricao': 'Avisos e eventos semanais',
                'icone': '📢',
                'prioridade': 100,
                'cor': '#FF6B6B',
                'auto_expiracao': True,
                'dias_expiracao': 7
            },
            {
                'nome': 'Acolhimento e Orientação',
                'slug': 'acolhimento',
                'tipo': 'estatico',
                'descricao': 'Orientações pastorais',
                'icone': '🤝',
                'prioridade': 70,
                'cor': '#9C27B0'
            }
        ]
        
        for dados in bases:
            base, created = KnowledgeBase.objects.get_or_create(
                slug=dados['slug'],
                defaults=dados
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Criada: {base.nome}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Já existe: {base.nome}')
                )
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Concluído!'))