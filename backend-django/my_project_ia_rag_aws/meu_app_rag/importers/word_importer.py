# conhecimento/importers/word_importer.py

from docx import Document as DocxDocument
import re
from typing import Dict, List, Optional

from ..rag.manager import KnowledgeManager
from ..models import KnowledgeBase, Documento


class WordImporter:
    """Importador de documentos Word"""

    INICIO = "---INÍCIO DO CONTEÚDO---"
    FIM = "---FIM DO CONTEÚDO---"

    def __init__(self):
        self.manager = KnowledgeManager()

    def processar_word(self, arquivo_path: str, base_slug: str) -> Documento:
        """
        Processa arquivo Word no formato padrão:

        Linha 1: TÍTULO
        CATEGORIA: nome
        TAGS: tag1, tag2
        ---INÍCIO DO CONTEÚDO---
        [conteúdo]
        ---FIM DO CONTEÚDO---
        """

        doc = DocxDocument(arquivo_path)
        texto = self._extrair_texto(doc)

        dados = self._parse_documento(texto)

        # Mantém padrão do sistema: base ativa
        base = KnowledgeBase.objects.get(slug=base_slug, ativo=True)

        documento = self.manager.adicionar_documento(
            base=base,
            titulo=dados["titulo"],
            conteudo=dados["conteudo"],
            categoria=dados.get("categoria", ""),
            tags=dados.get("tags", []),
        )

        return documento

    def _extrair_texto(self, doc: DocxDocument) -> str:
        """Extrai texto do Word (ignora parágrafos vazios)."""
        paragrafos = []
        for p in doc.paragraphs:
            t = (p.text or "").strip()
            if t:
                paragrafos.append(t)
        return "\n".join(paragrafos)

    def _parse_documento(self, texto: str) -> Dict:
        """Parse do formato estruturado."""
        linhas = [ln.strip() for ln in texto.split("\n") if ln.strip()]

        # 1) Título: primeira linha útil (não decorativa)
        titulo = None
        for linha in linhas:
            if linha and not linha.startswith("═"):
                titulo = linha
                break
        if not titulo:
            raise ValueError("Título não encontrado (primeira linha deve ser o título).")

        # 2) Categoria (case-insensitive, aceita espaços)
        categoria = ""
        for linha in linhas:
            m = re.match(r"^CATEGORIA\s*:\s*(.*)$", linha, flags=re.IGNORECASE)
            if m:
                categoria = (m.group(1) or "").strip()
                break

        # 3) Tags (case-insensitive, dedup + remove vazias)
        tags: List[str] = []
        for linha in linhas:
            m = re.match(r"^TAGS\s*:\s*(.*)$", linha, flags=re.IGNORECASE)
            if m:
                raw = (m.group(1) or "").strip()
                tags = self._parse_tags(raw)
                break

        # 4) Conteúdo entre marcadores (normaliza)
        conteudo = self._parse_conteudo(linhas)
        if not conteudo:
            raise ValueError("Conteúdo não encontrado entre os marcadores de início e fim.")

        return {
            "titulo": titulo,
            "categoria": categoria,
            "tags": tags,
            "conteudo": conteudo,
        }

    def _parse_tags(self, tags_str: str) -> List[str]:
        if not tags_str:
            return []
        parts = [t.strip() for t in tags_str.split(",")]
        # remove vazias e dedup case-insensitive preservando ordem
        out = []
        seen = set()
        for t in parts:
            if not t:
                continue
            k = t.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(t)
        return out

    def _parse_conteudo(self, linhas: List[str]) -> str:
        inicio_idx = None
        fim_idx = None

        # procura linhas exatas (após strip) para evitar variações
        for i, ln in enumerate(linhas):
            if ln == self.INICIO:
                inicio_idx = i
                continue
            if ln == self.FIM:
                fim_idx = i
                break

        if inicio_idx is None or fim_idx is None or fim_idx <= inicio_idx:
            raise ValueError(
                f"Formato inválido. O arquivo deve conter:\n"
                f"{self.INICIO}\n...\n{self.FIM}"
            )

        conteudo_linhas = linhas[inicio_idx + 1 : fim_idx]
        return "\n".join(conteudo_linhas).strip()
    