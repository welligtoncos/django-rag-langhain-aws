# conhecimento/tests/test_knowledge_manager.py

from django.test import TestCase

from my_project_ia_rag_aws.meu_app_rag.rag.manager import KnowledgeManager 


class KnowledgeManagerTest(TestCase):
    
    def setUp(self):
        self.manager = KnowledgeManager()
    
    def test_criar_base(self):
        """Testa criação de base"""
        base = self.manager.criar_base(
            nome="Secretaria",
            tipo="atualizavel",
            descricao="Serviços",
            icone="🏛️",
            prioridade=90
        )
        
        self.assertEqual(base.nome, "Secretaria")
        self.assertEqual(base.slug, "secretaria")
        self.assertTrue(base.ativo)
    
    def test_adicionar_documento(self):
        """Testa criação de documento"""
        base = self.manager.criar_base(
            nome="Test",
            tipo="estatico",
            descricao="Test"
        )
        
        doc = self.manager.adicionar_documento(
            base=base,
            titulo="Documento Teste",
            conteudo="Conteúdo de teste " * 10,
            categoria="Testes",
            tags=["teste", "exemplo"]
        )
        
        self.assertEqual(doc.titulo, "Documento Teste")
        self.assertEqual(doc.versao, 1)
        self.assertIsNotNone(doc.embedding)
    
    def test_atualizar_documento_com_versionamento(self):
        """Testa atualização com versionamento"""
        base = self.manager.criar_base(
            nome="Test",
            tipo="estatico",
            descricao="Test"
        )
        
        doc_v1 = self.manager.adicionar_documento(
            base=base,
            titulo="Versão 1",
            conteudo="Conteúdo versão 1 " * 10
        )
        
        doc_v2 = self.manager.atualizar_documento(
            documento_id=doc_v1.id,
            titulo="Versão 2",
            conteudo="Conteúdo versão 2 " * 10
        )
        
        # Verifica nova versão
        self.assertEqual(doc_v2.versao, 2)
        self.assertEqual(doc_v2.titulo, "Versão 2")
        self.assertEqual(doc_v2.documento_anterior.id, doc_v1.id)
        
        # Verifica v1 foi arquivada
        doc_v1.refresh_from_db()
        self.assertEqual(doc_v1.status, 'arquivado')
    
    def test_historico_documento(self):
        """Testa histórico de versões"""
        base = self.manager.criar_base(
            nome="Test",
            tipo="estatico",
            descricao="Test"
        )
        
        # Cria v1
        doc_v1 = self.manager.adicionar_documento(
            base=base,
            titulo="V1",
            conteudo="Conteúdo v1 " * 10
        )
        
        # Cria v2
        doc_v2 = self.manager.atualizar_documento(
            documento_id=doc_v1.id,
            titulo="V2",
            conteudo="Conteúdo v2 " * 10
        )
        
        # Cria v3
        doc_v3 = self.manager.atualizar_documento(
            documento_id=doc_v2.id,
            titulo="V3",
            conteudo="Conteúdo v3 " * 10
        )
        
        # Verifica histórico
        historico = self.manager.obter_historico_documento(doc_v3.id)
        
        self.assertEqual(len(historico), 3)
        self.assertEqual(historico[0].versao, 1)
        self.assertEqual(historico[1].versao, 2)
        self.assertEqual(historico[2].versao, 3)
    
    def test_restaurar_versao(self):
        """Testa restauração de versão"""
        base = self.manager.criar_base(
            nome="Test",
            tipo="estatico",
            descricao="Test"
        )
        
        doc_v1 = self.manager.adicionar_documento(
            base=base,
            titulo="Original",
            conteudo="Conteúdo original " * 10
        )
        
        doc_v2 = self.manager.atualizar_documento(
            documento_id=doc_v1.id,
            titulo="Editado",
            conteudo="Conteúdo editado " * 10
        )
        
        # Restaura v1
        doc_v3 = self.manager.restaurar_versao(
            documento_id=doc_v2.id,
            versao_numero=1
        )
        
        self.assertEqual(doc_v3.versao, 3)
        self.assertEqual(doc_v3.titulo, "Original")
        self.assertEqual(doc_v3.conteudo, doc_v1.conteudo)
    
    def test_regenerar_embeddings(self):
        """Testa regeneração de embeddings"""
        base = self.manager.criar_base(
            nome="Test",
            tipo="estatico",
            descricao="Test"
        )
        
        # Cria docs sem embedding
        doc1 = self.manager.adicionar_documento(
            base=base,
            titulo="Doc 1",
            conteudo="Conteúdo 1 " * 10,
            gerar_embedding=False
        )
        
        doc2 = self.manager.adicionar_documento(
            base=base,
            titulo="Doc 2",
            conteudo="Conteúdo 2 " * 10,
            gerar_embedding=False
        )
        
        # Verifica que não têm embedding
        self.assertIsNone(doc1.embedding)
        self.assertIsNone(doc2.embedding)
        
        # Regenera todos
        stats = self.manager.regenerar_todos_embeddings(base=base)
        
        self.assertEqual(stats['sucesso'], 2)
        
        # Verifica que agora têm embedding
        doc1.refresh_from_db()
        doc2.refresh_from_db()
        self.assertIsNotNone(doc1.embedding)
        self.assertIsNotNone(doc2.embedding)