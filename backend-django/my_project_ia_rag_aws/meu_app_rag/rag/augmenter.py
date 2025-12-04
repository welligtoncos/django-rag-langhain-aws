# conhecimento/rag/augmenter.py

from typing import List, Dict


class ContextAugmenter:
    """Formata contexto para o LLM"""
    
    def augment(self, query: str, documentos: List[Dict]) -> str:
        """
        Cria contexto estruturado
        
        Args:
            query: Consulta do usuário
            documentos: Lista de documentos encontrados
            
        Returns:
            Contexto formatado para Claude
        """
        # Agrupa por base
        docs_por_base = {}
        
        for doc in documentos:
            base_nome = doc['base']['nome']
            
            if base_nome not in docs_por_base:
                docs_por_base[base_nome] = {
                    'base_info': doc['base'],
                    'documentos': []
                }
            
            docs_por_base[base_nome]['documentos'].append(doc)
        
        # Constrói contexto
        partes = []
        
        # Header
        partes.append("CONSULTA DO USUÁRIO:")
        partes.append(f'"{query}"')
        partes.append("")
        partes.append("=" * 70)
        partes.append("")
        
        # Documentos por base
        for base_nome, info in docs_por_base.items():
            base = info['base_info']
            docs = info['documentos']
            
            partes.append(f"{base['icone']} BASE: {base_nome}")
            partes.append(f"Tipo: {base['tipo']}")
            partes.append(f"Total encontrado: {len(docs)}")
            partes.append("")
            
            for doc in docs:
                partes.append("─" * 70)
                partes.append(f"📄 {doc['titulo']}")
                
                if doc['categoria']:
                    partes.append(f"Categoria: {doc['categoria']}")
                
                if doc['tags']:
                    partes.append(f"Tags: {', '.join(doc['tags'])}")
                
                partes.append(f"🎯 Relevância: {doc['score']:.4f}")
                partes.append("")
                partes.append(doc['conteudo'])
                partes.append("")
                
                if doc['data_fim']:
                    partes.append(f"⏰ Válido até: {doc['data_fim'].strftime('%d/%m/%Y')}")
                    partes.append("")
            
            partes.append("")
        
        # Instruções
        partes.append("=" * 70)
        partes.append("INSTRUÇÕES IMPORTANTES:")
        partes.append("")
        partes.append("✅ Use APENAS as informações dos documentos acima")
        partes.append("✅ Seja objetivo e útil")
        partes.append("✅ Cite a base quando relevante")
        partes.append("✅ Se houver datas, mencione-as")
        partes.append("")
        partes.append("❌ NÃO invente informações")
        partes.append("❌ NÃO use conhecimento externo")
        partes.append("❌ Se não souber, diga que não encontrou")
        
        return "\n".join(partes)