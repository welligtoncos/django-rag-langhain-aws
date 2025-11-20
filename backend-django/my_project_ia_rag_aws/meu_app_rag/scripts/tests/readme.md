# 1. Salvar o script
# test_rag_stress.py

# 2. Instalar dependências
pip install requests

# 3. Certificar que a API está rodando
python manage.py runserver

# 4. Executar testes (em outro terminal)
python test_rag_stress.py
```

---

## 🎯 O QUE O SCRIPT TESTA

### **✅ 15 Suítes de Teste:**
```
1️⃣  Consultas Simples (10 testes)
2️⃣  Consultas com Características (10 testes)
3️⃣  Consultas por Preço (10 testes)
4️⃣  Consultas por Categoria (10 testes)
5️⃣  Consultas Complexas (10 testes)
6️⃣  Consultas de Comparação (10 testes)
7️⃣  Consultas de Disponibilidade (10 testes)
8️⃣  Consultas por Marca (10 testes)
9️⃣  Consultas de Recomendação (10 testes)
🔟 Edge Cases (20 testes)
1️⃣1️⃣ Consultas de Especificações (10 testes)
1️⃣2️⃣ Consultas Conversacionais (10 testes)
1️⃣3️⃣ Filtros Múltiplos (10 testes)
1️⃣4️⃣ Consultas de Análise (10 testes)
1️⃣5️⃣ Consultas Vagas (10 testes)

TOTAL: ~160 testes

{
  "stats": {
    "total": 160,
    "sucesso": 155,
    "erro": 5,
    "tempo_total": 245.3,
    "tempo_medio": 1.53,
    "tempo_min": 0.82,
    "tempo_max": 4.21,
    "throughput": 0.65
  },
  "resultados": [...],
  "erros": [...]
}