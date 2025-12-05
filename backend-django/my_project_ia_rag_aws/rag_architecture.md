# Arquitetura RAG e Tecnologias

Este documento detalha o funcionamento técnico do sistema de **Retrieval-Augmented Generation (RAG)** implementado neste projeto.

## 1. O Conceito RAG
RAG (Geração Aumentada por Recuperação) é uma técnica que une o poder de geração de texto dos LLMs (como o Claude ou GPT) com a precisão de uma base de dados própria.

Em vez de confiar apenas no "conhecimento treinado" do modelo (que pode estar desatualizado ou alucinar), o sistema:
1.  **Busca (Retrieve):** Encontra documentos relevantes na sua base de dados.
2.  **Aumenta (Augment):** Entrega esses documentos para a IA como contexto.
3.  **Gera (Generate):** A IA responde à pergunta do usuário baseada *apenas* no contexto fornecido.

---

## 2. Stack Tecnológico

### Backend & API
*   **Django 5:** Framework web robusto escrito em Python.
*   **Django Rest Framework (DRF):** Para expor a API REST.
*   **SQLite (Dev):** Banco de dados relacional (pode ser migrado para PostgreSQL).

### Inteligência Artificial (AWS Bedrock)
O projeto utiliza a infraestrutura da AWS Bedrock para acessar modelos de ponta via API.

*   **Embeddings (Vetorização):** `amazon.titan-embed-text-v2:0`
    *   Transforma textos (perguntas e documentos) em vetores numéricos de 1024 dimensões.
    *   Permite a busca semântica (entender o significado, não apenas palavras-chave).

*   **LLM (Geração de Texto):** `anthropic.claude-3-sonnet-20240229-v1:0`
    *   Modelo de linguagem avançado da Anthropic.
    *   Responsável por ler o contexto recuperado e formular a resposta final em linguagem natural.

---

## 3. Fluxo de Dados Detalhado

### A. Ingestão de Dados (Indexação)
Quando você cadastra um documento (via Admin, API ou Importação de Word):

1.  **Limpeza:** O texto é limpo e normalizado.
2.  **Vetorização:** O sistema envia o texto para o modelo **Titan Embeddings** na AWS.
3.  **Armazenamento:** O vetor resultante (embedding) é salvo no campo JSON do banco de dados, junto com o texto original.

### B. Processo de Consulta (Chat)
Quando o usuário faz uma pergunta ("Qual o horário da missa?"):

1.  **Embedding da Pergunta:** A pergunta é convertida em vetor pelo mesmo modelo Titan.
2.  **Busca Semântica (Retrieval):**
    *   O sistema compara o vetor da pergunta com todos os vetores dos documentos ativos.
    *   Utiliza **Similaridade de Cosseno** para calcular a proximidade.
    *   Filtra documentos por validade (data de expiração) e status.
    *   Seleciona os "Top K" documentos mais relevantes.
3.  **Montagem do Prompt (Augmentation):**
    *   O sistema cria um prompt para o LLM contendo:
        *   Instruções de comportamento ("Você é um assistente paroquial...").
        *   A pergunta do usuário.
        *   O conteúdo dos documentos recuperados.
4.  **Geração da Resposta:**
    *   O **Claude 3 Sonnet** recebe esse prompt.
    *   Ele analisa os documentos fornecidos e gera uma resposta precisa e fundamentada.
    *   Se a informação não estiver nos documentos, ele é instruído a dizer que não sabe (evitando alucinações).

---

## 4. Diferenciais Desta Implementação

*   **Multi-Base:** Capacidade de separar conhecimentos em "pastas" (ex: Secretaria, Liturgia, Eventos) e buscar em todas ou apenas em algumas.
*   **Validade Temporal:** Documentos podem ter data de validade (útil para avisos paroquiais que expiram).
*   **Priorização:** Bases podem ter pesos diferentes (ex: Avisos Urgentes aparecem primeiro).
*   **Híbrido:** Combina busca semântica (vetores) com filtros determinísticos (datas, categorias).
