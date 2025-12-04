import os
import sys
from pathlib import Path

import boto3
import django
from dotenv import load_dotenv  # pip install python-dotenv

# =========================
# Django bootstrap
# =========================
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

load_dotenv(ROOT / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project_ia_rag_aws.settings")
django.setup()

from meu_app_rag.rag.retriever import MultiBaseRetriever
from meu_app_rag.rag.augmenter import ContextAugmenter


def bedrock_client():
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
    profile = os.getenv("AWS_PROFILE")

    session = boto3.Session(profile_name=profile, region_name=region) if profile else boto3.Session(region_name=region)
    return session.client("bedrock-runtime")


def render_stream_and_collect(response_stream) -> str:
    """Imprime tokens em tempo real e também retorna o texto completo."""
    out = []
    for event in response_stream.get("stream", []):
        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"]["delta"]
            text = delta.get("text")
            if text:
                print(text, end="", flush=True)
                out.append(text)
    print()
    return "".join(out)


def main():
    model_id = (
        os.getenv("BEDROCK_CHAT_MODEL_ID")
        or os.getenv("BEDROCK_LLM_MODEL")
        or os.getenv("BEDROCK_MODEL_ID")
    )
    if not model_id:
        print("❌ Defina BEDROCK_CHAT_MODEL_ID (ou BEDROCK_LLM_MODEL / BEDROCK_MODEL_ID) no .env")
        return 1

    retriever = MultiBaseRetriever()
    augmenter = ContextAugmenter()
    brt = bedrock_client()

    # ✅ system precisa ser SEPARADO (não pode ser message role=system)
    system = [
        {
            "text": (
                "Você é um assistente de uma paróquia. "
                "Use o CONTEXTO fornecido quando ele for relevante. "
                "Se faltar informação, diga exatamente o que faltou e sugira onde obter."
            )
        }
    ]

    # histórico só com user/assistant
    history = []

    print("💬 Chat Bedrock + RAG (digite 'sair' para encerrar)")
    print("-" * 60)

    while True:
        pergunta = input("Você> ").strip()
        if not pergunta:
            continue
        if pergunta.lower() in {"sair", "exit", "quit"}:
            break

        # 1) retrieve
        docs = retriever.retrieve(query=pergunta, limit=3)

        # 2) augment
        contexto = augmenter.augment(pergunta, docs) if docs else ""

        if os.getenv("RAG_DEBUG") == "1":
            print("\n[debug] docs:", len(docs))
            for d in docs:
                print(" -", d.get("id"), d.get("titulo"), "score=", d.get("score"))
            print("[debug] contexto chars:", len(contexto))
            print()

        # 3) prompt
        if contexto:
            user_text = (
                f"PERGUNTA:\n{pergunta}\n\n"
                f"CONTEXTO (use somente se for relevante):\n{contexto}\n\n"
                "Responda em pt-BR, com passos claros e objetivo."
            )
        else:
            # fallback (não trava o chat)
            user_text = (
                f"PERGUNTA:\n{pergunta}\n\n"
                "Não há contexto disponível no banco agora. "
                "Responda de forma geral e diga quais informações específicas você precisaria "
                "para dar uma resposta exata da paróquia."
            )

        messages = history + [{"role": "user", "content": [{"text": user_text}]}]

        try:
            resp = brt.converse_stream(
                modelId=model_id,
                system=system,  # ✅ aqui
                messages=messages,
                inferenceConfig={"temperature": 0.2, "maxTokens": 800},
            )

            print("Assistente> ", end="", flush=True)
            assistant_text = render_stream_and_collect(resp)

            # 4) salva histórico completo (user + assistant) pra manter conversa real
            history.append({"role": "user", "content": [{"text": pergunta}]})
            history.append({"role": "assistant", "content": [{"text": assistant_text}]})

            # limita histórico
            if len(history) > 12:
                history = history[-12:]

        except Exception as e:
            print(f"❌ Erro Bedrock: {e}")
            print("Dica: verifique região, acesso ao modelo (Model access) e permissões IAM.")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
