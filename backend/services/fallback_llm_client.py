"""
backend/services/fallback_llm_client.py
Tier 2 of the Explainability Agent's 3-tier cascade.
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

FALLBACK_MODEL = os.environ.get(
    "FALLBACK_EXPLAINABILITY_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free"
)
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT_SECONDS = 60


def call_fallback_llm(prompt: str) -> dict:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    try:
        response = requests.post(
            OPENROUTER_CHAT_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": FALLBACK_MODEL,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        message = data["choices"][0]["message"]
        content = (message.get("content") or "").strip()
        if not content:
            return {
                "success": False, "model": FALLBACK_MODEL, "content": None,
                "usage": None, "reasoning_details": [],
                "error": "empty response from fallback model",
            }
        usage = data.get("usage", {}) or {}
        return {
            "success": True, "model": FALLBACK_MODEL, "content": content,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            "reasoning_details": message.get("reasoning_details", []),
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        logger.error("[fallback_llm_client] Call to %s failed: %s", FALLBACK_MODEL, exc)
        return {
            "success": False, "model": FALLBACK_MODEL, "content": None,
            "usage": None, "reasoning_details": [], "error": str(exc),
        }
