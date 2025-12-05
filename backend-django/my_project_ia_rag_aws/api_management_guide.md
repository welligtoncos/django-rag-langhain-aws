# Guia de Gerenciamento via API

Este guia explica como usar a API REST para criar, listar, atualizar e deletar Bases de Conhecimento e Documentos.

**Base URL:** `http://localhost:8000/api/`

---

## 1. Gerenciando Bases de Conhecimento

### Listar todas as bases
*   **Método:** `GET`
*   **URL:** `/bases/`

### Criar uma nova base
*   **Método:** `POST`
*   **URL:** `/bases/`
*   **Body (JSON):**
    ```json
    {
      "nome": "Catequese",
      "descricao": "Materiais para catequistas e alunos",
      "tipo": "atualizavel",
      "icone": "✝️",
      "cor": "#FF5733",
      "ativo": true
    }
    ```

### Detalhes de uma base
*   **Método:** `GET`
*   **URL:** `/bases/{slug}/`
    *   *Exemplo:* `/bases/catequese/`

### Atualizar uma base
*   **Método:** `PATCH`
*   **URL:** `/bases/{slug}/`
*   **Body (JSON):**
    ```json
    {
      "descricao": "Nova descrição atualizada",
      "icone": "📖"
    }
    ```

### Deletar uma base
*   **Método:** `DELETE`
*   **URL:** `/bases/{slug}/`

---

## 2. Gerenciando Documentos

### Listar documentos de uma base
*   **Método:** `GET`
*   **URL:** `/documentos/?base={slug_da_base}`
    *   *Exemplo:* `/documentos/?base=catequese`

### Criar um novo documento
*   **Método:** `POST`
*   **URL:** `/documentos/`
*   **Body (JSON):**
    ```json
    {
      "base": 1,  // ID da base (ou use a interface para ver o ID)
      "titulo": "Horários da Catequese 2024",
      "conteudo": "A catequese infantil acontece aos sábados às 09h.",
      "categoria": "Horários",
      "tags": ["sabado", "infantil"],
      "status": "ativo"
    }
    ```
    > **Nota:** O campo `base` exige o ID numérico da base. Para descobrir o ID, consulte o endpoint `/bases/`.

### Atualizar um documento
*   **Método:** `PATCH`
*   **URL:** `/documentos/{id}/`
*   **Body (JSON):**
    ```json
    {
      "conteudo": "Novo conteúdo atualizado...",
      "status": "arquivado"
    }
    ```

### Deletar um documento
*   **Método:** `DELETE`
*   **URL:** `/documentos/{id}/`

---

## 3. Dicas Úteis

*   **Filtros:** Você pode filtrar documentos por status ou categoria:
    *   `/documentos/?status=ativo`
    *   `/documentos/?categoria=Liturgia`
*   **Paginação:** A API retorna resultados paginados. Use `?page=2` para navegar.
