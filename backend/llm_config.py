"""
backend/llm_config.py
Two separate LLM clients, deliberately using different models suited to
their different jobs.

1. llm_explainability -- OpenRouter, openai/gpt-oss-20b:free. Used ONLY by
   backend/agents/explainability_agent.py for short, RAG-grounded clinical
   rationales.
2. llm_chat_assistant -- Groq, openai/gpt-oss-120b. Used ONLY by the AI
   Governance Assistant chatbot (backend/services/chat_agent_service.py),
   which needs genuine multi-step tool-calling.

No agent outside explainability_agent.py may import llm_explainability,
and no code outside the chat assistant may import llm_chat_assistant.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI

llm_explainability = ChatOpenAI(
    model=os.environ.get("EXPLAINABILITY_MODEL", "openai/gpt-oss-20b:free"),
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "sk-or-placeholder"),
    temperature=0.2,
    max_tokens=1024,
)

llm_chat_assistant = ChatOpenAI(
    model=os.environ.get("CHAT_ASSISTANT_MODEL", "openai/gpt-oss-120b"),
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY", "gsk-placeholder"),
    temperature=0.2,
    max_tokens=1024,
)
