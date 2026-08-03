"""
backend/llm_config.py
The ONLY LLM client in this system. Imported exclusively by
backend/agents/explainability_agent.py -- no other agent may instantiate
an LLM client (Lineage, Compliance, and Twin Assembler are fully
deterministic, see PRD Section 11.3).

Uses OpenRouter's OpenAI-compatible endpoint. Default model is the free
openai/gpt-oss-20b:free; swap EXPLAINABILITY_MODEL in .env to
openai/gpt-4o (or any other OpenRouter model) with no code change.
"""
import os

from langchain_openai import ChatOpenAI

llm_explainability = ChatOpenAI(
    model=os.environ.get("EXPLAINABILITY_MODEL", "openai/gpt-oss-20b:free"),
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY", "sk-or-placeholder"),
    temperature=0.2,
    max_tokens=1024,
)
