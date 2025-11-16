import os
from pathlib import Path

# Base do projeto Django
BASE_DIR = Path(__file__).resolve().parent.parent

# Diretório para dados (embeddings, cache, etc)
DATA_DIR = BASE_DIR / 'db_data'
DATA_DIR.mkdir(exist_ok=True)

# ==============================================
# AWS CONFIGURAÇÕES
# ==============================================
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')

# ==============================================
# BEDROCK CONFIGURAÇÕES
# ==============================================
# Modelo para geração de texto
BEDROCK_MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'

# Modelo para embeddings
BEDROCK_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"

# Parâmetros de geração
MAX_TOKENS = 500
TEMPERATURE = 0.5
TOP_P = 0.9

# ==============================================
# APLICAÇÃO CONFIGURAÇÕES
# ==============================================
APP_NAME = "Assistente Virtual de Produtos"
APP_VERSION = "1.0.0"
HISTORICO_MAX = 10

# ==============================================
# RAG CONFIGURAÇÕES
# ==============================================
# Arquivos de cache
CATALOGO_PKL = str(DATA_DIR / 'catalogo.pkl')
VECTORS_PKL = str(DATA_DIR / 'vectors.pkl')

# Limites de busca
RAG_DEFAULT_LIMIT = 5
RAG_MAX_LIMIT = 20

# Threshold de similaridade (0.0 a 1.0)
RAG_SIMILARITY_THRESHOLD = 0.3
 