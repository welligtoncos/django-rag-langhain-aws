from typing import List, Dict, Union, Optional
from decimal import Decimal


class ContextAugmenter:
    """
    RAG - Augmentation: Gera contexto estruturado para o LLM.
    
    Funcionalidades:
    - Formatação de produtos para o LLM
    - Contexto conciso ou detalhado
    - Contexto de comparação
    - Highlighting de promoções e avaliações
    - Suporte a imagens
    - Estatísticas do contexto
    """

    # Emojis para destacar informações
    EMOJI_PROMOCAO = "🔥"
    EMOJI_PRECO = "💰"
    EMOJI_ESTOQUE = "📦"
    EMOJI_AVALIACAO = "⭐"
    EMOJI_RELEVANCIA = "🎯"
    EMOJI_IMAGEM = "📸"
    EMOJI_MARCA = "🏷️"
    EMOJI_DESCRICAO = "📝"
    EMOJI_ESPECIFICACOES = "📋"

    @staticmethod
    def _safe(value, default="N/A"):
        """
        Retorna valor seguro, evitando None ou vazios.
        
        Args:
            value: Valor a verificar
            default: Valor padrão se inválido
            
        Returns:
            str: Valor seguro
        """
        if value is None or str(value).strip() in ("", "null", "None"):
            return default
        return str(value).strip()

    @staticmethod
    def _formatar_preco(preco: Union[float, Decimal, int]) -> str:
        """
        Formata preço em Real brasileiro.
        
        Args:
            preco: Valor numérico
            
        Returns:
            str: Preço formatado (ex: R$ 199,90)
        """
        if preco is None:
            return "N/A"
        
        try:
            valor = float(preco)
            # Formato brasileiro: R$ 1.234,56
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return "N/A"

    @staticmethod
    def _calcular_desconto(preco: float, preco_promocional: float) -> float:
        """
        Calcula percentual de desconto.
        
        Args:
            preco: Preço original
            preco_promocional: Preço em promoção
            
        Returns:
            float: Percentual de desconto
        """
        if preco <= 0 or preco_promocional >= preco:
            return 0.0
        
        return ((preco - preco_promocional) / preco) * 100

    @staticmethod
    def _extrair_dados(produto) -> Dict:
        """
        Extrai dados de produto (dict ou Django model).
        
        Args:
            produto: Dict ou objeto Django Model
            
        Returns:
            dict: Dados normalizados do produto
        """
        if hasattr(produto, '__dict__'):
            # É um objeto Django Model
            return {
                'id': produto.id,
                'nome': produto.nome,
                'categoria': produto.categoria,
                'subcategoria': produto.subcategoria,
                'preco': float(produto.preco) if produto.preco else 0,
                'preco_promocional': float(produto.preco_promocional) if produto.preco_promocional else None,
                'marca': produto.marca,
                'cor': produto.cor,
                'tamanho': produto.tamanho,
                'material': getattr(produto, 'material', None),
                'estoque': produto.estoque,
                'avaliacao': float(produto.avaliacao) if produto.avaliacao else None,
                'num_avaliacoes': produto.num_avaliacoes,
                'descricao': produto.descricao,
                'especificacoes': produto.especificacoes,
                'imagem': getattr(produto, 'imagem', None),
                'imagem_url': getattr(produto, 'imagem_url', None),
                'imagem_completa': getattr(produto, 'imagem_completa', None),
                'score': getattr(produto, 'score', 0),
                'score_percentual': getattr(produto, 'score_percentual', None)
            }
        else:
            # É um dict
            return produto

    @classmethod
    def format_product(
        cls, 
        produto,
        modo: str = "completo",
        incluir_imagem: bool = True
    ) -> str:
        """
        Formata um produto para exibição no contexto do LLM.
        
        Args:
            produto: dict ou objeto Produto do Django
            modo: 'conciso' ou 'completo'
            incluir_imagem: Se deve incluir URL da imagem
            
        Returns:
            str: Produto formatado
        """
        p = cls._extrair_dados(produto)

        # Processar preços
        preco = float(p.get("preco") or 0)
        preco_prom = p.get("preco_promocional")
        preco_prom = float(preco_prom) if preco_prom else None

        # Informações de promoção
        if preco_prom and preco_prom < preco:
            preco_exibir = preco_prom
            desconto_pct = cls._calcular_desconto(preco, preco_prom)
            promocao_txt = (
                f"{cls.EMOJI_PROMOCAO} PROMOÇÃO ATIVA!\n"
                f"De {cls._formatar_preco(preco)} por {cls._formatar_preco(preco_prom)} "
                f"(Economia de {desconto_pct:.0f}%)"
            )
            tem_promocao = True
        else:
            preco_exibir = preco
            promocao_txt = None
            tem_promocao = False

        # Score de relevância
        score = float(p.get('score') or 0)
        score_pct = p.get('score_percentual')
        if not score_pct and score > 0:
            score_pct = f"{score * 100:.1f}%"

        # Avaliação
        avaliacao = p.get('avaliacao')
        num_avaliacoes = p.get('num_avaliacoes', 0)
        
        avaliacao_txt = cls._safe(avaliacao, "N/A")
        if avaliacao and float(avaliacao) >= 4.5:
            avaliacao_txt += f" {cls.EMOJI_AVALIACAO} EXCELENTE!"
        
        # Estoque
        estoque = p.get('estoque', 0)
        if estoque < 10 and estoque > 0:
            estoque_txt = f"{estoque} unidades ⚠️ ESTOQUE BAIXO!"
        elif estoque == 0:
            estoque_txt = "0 unidades ❌ ESGOTADO"
        else:
            estoque_txt = f"{estoque} unidades"

        # Modo conciso
        if modo == "conciso":
            linhas = [
                f"═══ {p.get('nome')} ═══",
                f"{cls.EMOJI_PRECO} Preço: {cls._formatar_preco(preco_exibir)}",
            ]
            
            if tem_promocao:
                linhas.append(f"{cls.EMOJI_PROMOCAO} {desconto_pct:.0f}% OFF")
            
            if avaliacao:
                linhas.append(f"{cls.EMOJI_AVALIACAO} {avaliacao}/5.0 ({num_avaliacoes} avaliações)")
            
            linhas.append(f"{cls.EMOJI_ESTOQUE} {estoque_txt}")
            linhas.append(f"{cls.EMOJI_RELEVANCIA} Relevância: {score_pct or f'{score:.2f}'}")
            
            return "\n".join(linhas)

        # Modo completo (padrão)
        linhas = [
            "=" * 60,
            f"PRODUTO #{p.get('id')}",
            "=" * 60,
            f"📦 NOME: {p.get('nome')}",
            "",
            "🏷️ CATEGORIZAÇÃO:",
            f"  • Categoria: {cls._safe(p.get('categoria'))}",
            f"  • Subcategoria: {cls._safe(p.get('subcategoria'))}",
            f"  • Marca: {cls._safe(p.get('marca'))}",
            "",
            "💰 PREÇOS:",
            f"  • Preço atual: {cls._formatar_preco(preco_exibir)}",
        ]

        if promocao_txt:
            linhas.append(f"  • {promocao_txt}")

        linhas.extend([
            "",
            "🎨 CARACTERÍSTICAS:",
            f"  • Cor: {cls._safe(p.get('cor'))}",
            f"  • Tamanho: {cls._safe(p.get('tamanho'))}",
        ])

        material = p.get('material')
        if material:
            linhas.append(f"  • Material: {cls._safe(material)}")

        linhas.extend([
            "",
            f"📦 DISPONIBILIDADE:",
            f"  • Estoque: {estoque_txt}",
            "",
            f"⭐ AVALIAÇÕES:",
            f"  • Nota: {avaliacao_txt} / 5.0",
            f"  • Avaliadores: {num_avaliacoes} pessoas",
            "",
        ])

        # Descrição
        descricao = p.get('descricao')
        if descricao and str(descricao).strip() not in ("", "N/A"):
            linhas.extend([
                "📝 DESCRIÇÃO:",
                f"  {descricao}",
                "",
            ])

        # Especificações
        especificacoes = p.get('especificacoes')
        if especificacoes and str(especificacoes).strip() not in ("", "N/A"):
            linhas.extend([
                "📋 ESPECIFICAÇÕES:",
                f"  {especificacoes}",
                "",
            ])

        # Imagem
        if incluir_imagem:
            imagem_url = p.get('imagem_completa') or p.get('imagem_url')
            if imagem_url:
                linhas.extend([
                    f"{cls.EMOJI_IMAGEM} IMAGEM:",
                    f"  {imagem_url}",
                    "",
                ])

        # Relevância
        linhas.extend([
            f"{cls.EMOJI_RELEVANCIA} RELEVÂNCIA PARA SUA BUSCA:",
            f"  • Score: {score_pct or f'{score:.4f}'}",
        ])

        return "\n".join(linhas)

    @classmethod
    def format_product_comparacao(cls, produtos: List) -> str:
        """
        Formata produtos lado a lado para comparação.
        
        Args:
            produtos: Lista de produtos (2-4 produtos)
            
        Returns:
            str: Comparação formatada
        """
        if not produtos:
            return "Nenhum produto para comparar."

        if len(produtos) > 4:
            produtos = produtos[:4]  # Limitar a 4 produtos

        linhas = [
            "=" * 80,
            f"COMPARAÇÃO DE {len(produtos)} PRODUTOS",
            "=" * 80,
            ""
        ]

        for i, produto in enumerate(produtos, 1):
            p = cls._extrair_dados(produto)
            
            preco = float(p.get("preco") or 0)
            preco_prom = p.get("preco_promocional")
            preco_final = float(preco_prom) if preco_prom else preco
            
            linhas.append(f"\n🔸 OPÇÃO {i}: {p.get('nome')}")
            linhas.append(f"   Preço: {cls._formatar_preco(preco_final)}")
            
            if preco_prom:
                desconto = cls._calcular_desconto(preco, preco_prom)
                linhas.append(f"   {cls.EMOJI_PROMOCAO} Desconto: {desconto:.0f}% OFF")
            
            linhas.append(f"   Avaliação: {cls._safe(p.get('avaliacao'))}⭐")
            linhas.append(f"   Estoque: {p.get('estoque', 0)} unidades")
            linhas.append(f"   Marca: {cls._safe(p.get('marca'))}")

        return "\n".join(linhas)

    @classmethod
    def augment(
        cls, 
        produtos: List,
        query: str,
        modo: str = "completo",
        incluir_instrucoes: bool = True
    ) -> str:
        """
        Gera contexto completo para o LLM.
        
        Args:
            produtos: Lista de produtos encontrados
            query: Consulta original do usuário
            modo: 'conciso' ou 'completo'
            incluir_instrucoes: Se deve incluir instruções ao LLM
            
        Returns:
            str: Contexto formatado para o LLM
        """
        if not produtos:
            return (
                f"❌ NENHUM PRODUTO ENCONTRADO\n\n"
                f"Consulta do usuário: \"{query}\"\n\n"
                f"📝 SUGESTÃO:\n"
                f"Peça ao usuário para:\n"
                f"• Reformular a busca com termos mais gerais\n"
                f"• Buscar por categoria (Roupas, Eletrônicos, Beleza, etc.)\n"
                f"• Especificar faixa de preço\n"
                f"• Mencionar outras características desejadas"
            )

        # Cabeçalho
        linhas = [
            "╔" + "=" * 78 + "╗",
            f"║ 🔍 CONSULTA DO USUÁRIO: \"{query}\"",
            "╚" + "=" * 78 + "╝",
            "",
            f"📊 RESULTADOS: {len(produtos)} produto(s) encontrado(s)",
            "",
        ]

        # Estatísticas rápidas
        precos = [float(p.get('preco') or 0) for p in 
                  [cls._extrair_dados(p) for p in produtos]]
        promocoes = sum(1 for p in [cls._extrair_dados(p) for p in produtos] 
                       if p.get('preco_promocional'))
        
        if precos:
            linhas.extend([
                "💰 FAIXA DE PREÇOS:",
                f"  • Mais barato: {cls._formatar_preco(min(precos))}",
                f"  • Mais caro: {cls._formatar_preco(max(precos))}",
                f"  • Preço médio: {cls._formatar_preco(sum(precos)/len(precos))}",
                "",
            ])

        if promocoes > 0:
            linhas.append(f"🔥 {promocoes} produto(s) em PROMOÇÃO!")
            linhas.append("")

        # Produtos formatados
        linhas.append("📦 PRODUTOS DISPONÍVEIS (ORDENADOS POR RELEVÂNCIA):")
        linhas.append("")

        for i, produto in enumerate(produtos, 1):
            linhas.append(f"\n{'─' * 60}")
            linhas.append(f"PRODUTO {i} DE {len(produtos)}")
            linhas.append('─' * 60)
            linhas.append(cls.format_product(produto, modo=modo))
            linhas.append("")

        # Instruções para o LLM
        if incluir_instrucoes:
            linhas.extend([
                "",
                "╔" + "=" * 78 + "╗",
                "║ 📋 INSTRUÇÕES PARA O ASSISTENTE",
                "╚" + "=" * 78 + "╝",
                "",
                "✅ DEVE FAZER:",
                "  1. Usar APENAS os produtos listados acima",
                "  2. Destacar promoções quando disponíveis (🔥)",
                "  3. Mencionar estoque baixo se relevante (< 10 unidades)",
                "  4. Considerar avaliações dos usuários (⭐)",
                "  5. Comparar produtos quando houver múltiplas opções",
                "  6. Ser objetivo, claro e amigável",
                "  7. Recomendar o melhor custo-benefício",
                "",
                "❌ NÃO DEVE FAZER:",
                "  1. Inventar produtos, marcas, preços ou características",
                "  2. Usar conhecimento externo ao catálogo fornecido",
                "  3. Afirmar disponibilidade de produtos não listados",
                "  4. Prometer prazos de entrega (não temos essa info)",
                "",
                "💡 SE O USUÁRIO PEDIR ALGO FORA DO CATÁLOGO:",
                '  → "Não encontrei esse item específico no catálogo atual."',
                '  → "Posso sugerir alternativas similares?"',
                "",
            ])

        return "\n".join(linhas)

    @classmethod
    def augment_conciso(cls, produtos: List, query: str) -> str:
        """Versão concisa do contexto (para respostas rápidas)"""
        return cls.augment(produtos, query, modo="conciso", incluir_instrucoes=False)

    @classmethod
    def augment_comparacao(cls, produtos: List, query: str) -> str:
        """Contexto específico para comparação de produtos"""
        if not produtos:
            return "Nenhum produto para comparar."

        linhas = [
            f"CONSULTA: {query}",
            "",
            cls.format_product_comparacao(produtos),
            "",
            "📊 ANÁLISE PARA COMPARAÇÃO:",
            "",
            "Por favor, compare os produtos acima considerando:",
            "  1. Melhor custo-benefício (preço vs qualidade)",
            "  2. Avaliações e satisfação dos clientes",
            "  3. Disponibilidade em estoque",
            "  4. Promoções ativas",
            "  5. Características únicas de cada produto",
            "",
            "Forneça uma recomendação clara baseada nas necessidades do cliente.",
        ]

        return "\n".join(linhas)

    @classmethod
    def get_statistics(cls, produtos: List) -> Dict:
        """
        Retorna estatísticas do contexto gerado.
        
        Args:
            produtos: Lista de produtos
            
        Returns:
            dict: Estatísticas do contexto
        """
        if not produtos:
            return {
                "total_produtos": 0,
                "com_promocao": 0,
                "estoque_total": 0,
                "preco_minimo": 0,
                "preco_maximo": 0,
                "preco_medio": 0,
                "avaliacao_media": 0
            }

        produtos_norm = [cls._extrair_dados(p) for p in produtos]
        
        precos = [float(p.get('preco') or 0) for p in produtos_norm]
        promocoes = sum(1 for p in produtos_norm if p.get('preco_promocional'))
        estoque = sum(int(p.get('estoque') or 0) for p in produtos_norm)
        avaliacoes = [float(p.get('avaliacao') or 0) for p in produtos_norm if p.get('avaliacao')]

        return {
            "total_produtos": len(produtos),
            "com_promocao": promocoes,
            "estoque_total": estoque,
            "preco_minimo": min(precos) if precos else 0,
            "preco_maximo": max(precos) if precos else 0,
            "preco_medio": sum(precos) / len(precos) if precos else 0,
            "avaliacao_media": sum(avaliacoes) / len(avaliacoes) if avaliacoes else 0
        }