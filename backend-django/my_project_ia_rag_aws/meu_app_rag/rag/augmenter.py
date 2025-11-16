class ContextAugmenter:
    """Gera contexto estruturado e limpo para uso no RAG."""

    @staticmethod
    def _safe(value, default="N/A"):
        """Retorna valor seguro, evitando None ou vazios"""
        if value is None or str(value).strip() in ("", "null", "None"):
            return default
        return value

    @staticmethod
    def format_product(produto):
        """
        Formata um produto para exibição no contexto do LLM.
        
        Args:
            produto: dict ou objeto Produto do Django
            
        Returns:
            str: Produto formatado
        """
        # Suporta tanto dict quanto objeto Django
        if hasattr(produto, '__dict__'):
            # É um objeto Django Model
            p = {
                'id': produto.id,
                'nome': produto.nome,
                'categoria': produto.categoria,
                'subcategoria': produto.subcategoria,
                'preco': float(produto.preco) if produto.preco else 0,
                'preco_promocional': float(produto.preco_promocional) if produto.preco_promocional else None,
                'marca': produto.marca,
                'cor': produto.cor,
                'tamanho': produto.tamanho,
                'estoque': produto.estoque,
                'avaliacao': float(produto.avaliacao) if produto.avaliacao else None,
                'num_avaliacoes': produto.num_avaliacoes,
                'descricao': produto.descricao,
                'especificacoes': produto.especificacoes,
                'score': getattr(produto, 'score', 0)
            }
        else:
            # É um dict
            p = produto

        preco = float(p.get("preco") or 0)
        preco_prom = p.get("preco_promocional")
        preco_prom = float(preco_prom) if preco_prom else None

        if preco_prom:
            preco_exibir = preco_prom
            desconto_pct = ((preco - preco_prom) / preco * 100) if preco > 0 else 0
            promocao_txt = f"🔥 PROMOÇÃO: De R$ {preco:.2f} por R$ {preco_prom:.2f} ({desconto_pct:.0f}% OFF)"
        else:
            preco_exibir = preco
            promocao_txt = "Sem promoção no momento"

        return f"""
=== PRODUTO ===
ID: {p.get('id')}
Nome: {p.get('nome')}
Categoria: {ContextAugmenter._safe(p.get('categoria'))}
Subcategoria: {ContextAugmenter._safe(p.get('subcategoria'))}
💰 Preço: R$ {preco_exibir:.2f}
{promocao_txt}
Marca: {ContextAugmenter._safe(p.get('marca'))}
Cor: {ContextAugmenter._safe(p.get('cor'))}
Tamanho: {ContextAugmenter._safe(p.get('tamanho'))}
📦 Estoque: {ContextAugmenter._safe(p.get('estoque'))} unidades
⭐ Avaliação: {ContextAugmenter._safe(p.get('avaliacao'))} / 5.0
👥 Avaliações: {ContextAugmenter._safe(p.get('num_avaliacoes'))} pessoas avaliaram
📝 Descrição: {ContextAugmenter._safe(p.get('descricao'))}
📋 Especificações: {ContextAugmenter._safe(p.get('especificacoes'))}
🎯 Relevância: {float(p.get('score') or 0):.4f}
""".strip()

    @classmethod
    def augment(cls, produtos, query):
        """
        Gera contexto completo para o LLM a partir dos produtos encontrados.
        
        Args:
            produtos: Lista de produtos encontrados
            query: Consulta original do usuário
            
        Returns:
            str: Contexto formatado para o LLM
        """
        if not produtos:
            return (
                f"Nenhum produto encontrado para a consulta: '{query}'. "
                "Peça ao usuário mais detalhes ou outra característica."
            )

        blocos = [cls.format_product(prod) for prod in produtos]
        contexto_produtos = "\n\n".join(blocos)

        return f"""
CONSULTA DO USUÁRIO:
"{query}"

PRODUTOS ENCONTRADOS (ORDENADOS POR RELEVÂNCIA):
Total de produtos: {len(produtos)}

{contexto_produtos}

INSTRUÇÕES PARA O ASSISTENTE:
✅ Use APENAS os produtos listados acima
✅ Destaque promoções quando disponíveis
✅ Mencione estoque baixo se relevante (< 10 unidades)
✅ Considere as avaliações dos usuários
✅ Seja objetivo e útil
❌ NÃO invente informações, marcas, preços ou características
❌ Se o usuário pedir algo fora dessa lista, responda: "Não encontrei esse item no catálogo atual"
""".strip()