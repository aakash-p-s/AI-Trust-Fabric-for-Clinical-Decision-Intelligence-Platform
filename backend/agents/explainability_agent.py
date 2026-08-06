"""
backend/agents/explainability_agent.py
3-tier cascade + RAG grounding with safe error handling.
"""
import logging
import os
import time

from backend.agents.state import AgentState
from backend.services import fallback_llm_client, rag_service

logger = logging.getLogger(__name__)

AGENT_NAME = "explainability_agent"
LOW_GROUNDING_THRESHOLD = 0.40
MAX_RETRIES = 1
MIN_RESPONSE_LENGTH = 20
PRIMARY_MODEL_NAME = os.environ.get("EXPLAINABILITY_MODEL", "openai/gpt-oss-20b:free")
RAG_TOP_K = 3


def explainability_node(state: AgentState) -> AgentState:
    pred = state["prediction_input"]
    patient = state["patient_context"]

    retrieved, rag_error = _retrieve_safely(pred, patient)
    prompt = _build_prompt(pred, patient, retrieved)

    started_at = time.monotonic()
    attempts = []

    primary = _try_primary(prompt)
    attempts.append(primary["attempt"])

    if primary["success"]:
        final_text = primary["content"]
        final_source = "primary_llm"
        model_used = PRIMARY_MODEL_NAME
        token_usage = primary["usage"]
    else:
        fallback = fallback_llm_client.call_fallback_llm(prompt)
        attempts.append({
            "model": fallback["model"],
            "status": "success" if fallback["success"] else "failed",
            "reason": fallback["error"],
        })
        if fallback["success"]:
            final_text = fallback["content"]
            final_source = "fallback_llm"
            model_used = fallback["model"]
            token_usage = fallback["usage"]
        else:
            final_text = _fallback_explanation(pred, patient)
            final_source = "deterministic_fallback"
            model_used = None
            token_usage = None

    duration_ms = int((time.monotonic() - started_at) * 1000)
    best_score = max((r["similarity_score"] for r in retrieved), default=0.0)

    if rag_error or not retrieved:
        rag_status = "unavailable"
    elif best_score < LOW_GROUNDING_THRESHOLD:
        rag_status = "degraded"
    else:
        rag_status = "live"

    explanation = {
        "text": final_text,
        "explanation_type": (
            "fallback_deterministic" if final_source == "deterministic_fallback"
            else "narrative_llm_rag_grounded"
        ),
        "grounded_in_sources": [
            {"id": r["id"], "source": r["source"], "similarity_score": r["similarity_score"]}
            for r in retrieved
        ],
        "low_grounding_confidence": best_score < LOW_GROUNDING_THRESHOLD,
        "rag": {
            "status": rag_status,
            "chunks_found": len(retrieved),
            "top_similarity_score": round(best_score, 4),
            "error": rag_error,
        },
        "cascade": {
            "final_source": final_source,
            "model_used": model_used,
            "attempts": attempts,
            "token_usage": token_usage,
            "duration_ms": duration_ms,
        },
    }
    return {**state, "explanation": explanation}


def _retrieve_safely(pred: dict, patient: dict) -> tuple[list[dict], str | None]:
    try:
        retrieved = rag_service.retrieve(
            prediction_label=pred["prediction"], symptoms=patient["symptoms"], top_k=RAG_TOP_K,
        )
        return retrieved, None
    except Exception as exc:  # noqa: BLE001
        logger.error("[%s] RAG retrieval failed: %s", AGENT_NAME, exc)
        return [], str(exc)


def _try_primary(prompt: str) -> dict:
    response_text = ""
    error_reason = None
    response = None

    for attempt_num in range(MAX_RETRIES + 1):
        try:
            from backend.llm_config import llm_explainability

            response = llm_explainability.invoke(prompt)
            response_text = (response.content or "").strip()
        except Exception as exc:  # noqa: BLE001
            logger.error("[%s] Primary LLM call failed (attempt %d): %s", AGENT_NAME, attempt_num + 1, exc)
            error_reason = str(exc)
            response_text = ""
            break

        if len(response_text) >= MIN_RESPONSE_LENGTH or attempt_num == MAX_RETRIES:
            if not response_text:
                error_reason = "empty response after retry"
            break
        logger.warning(
            "[%s] Primary response too short (%d chars) -- retry %d/%d",
            AGENT_NAME, len(response_text), attempt_num + 1, MAX_RETRIES,
        )

    if response_text:
        usage = _extract_token_usage(response)
        return {
            "success": True, "content": response_text, "usage": usage,
            "attempt": {"model": PRIMARY_MODEL_NAME, "status": "success", "reason": None},
        }
    return {
        "success": False, "content": "", "usage": None,
        "attempt": {"model": PRIMARY_MODEL_NAME, "status": "failed", "reason": error_reason},
    }


def _extract_token_usage(response) -> dict | None:
    try:
        usage = response.response_metadata.get("token_usage", {})
        if not usage:
            return None
        return {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
    except Exception:  # noqa: BLE001
        return None


def _build_prompt(pred: dict, patient: dict, retrieved: list[dict]) -> str:
    if retrieved:
        facts_text = "\n".join(f"- {f['text']} (source: {f['source']})" for f in retrieved)
    else:
        facts_text = "(No retrieved facts are available. State that clearly rather than inventing a clinical basis.)"
    return f"""You are assisting a clinician in understanding an AI diagnostic prediction.

Use ONLY the clinical facts listed below and the patient's data. Do not
state any clinical claim not directly supported by these facts. If the
patient's symptoms are not well explained by the facts, say so explicitly
rather than inventing a connection. This is a supporting explanation, not
a diagnosis.

Retrieved clinical facts:
{facts_text}

Patient: age {patient['age']}, symptoms: {', '.join(patient['symptoms'])}.
History: {patient['relevant_history']}.
Model prediction: {pred['prediction']}, confidence {pred['confidence']}.

Write a short, plain-English clinical rationale (2-4 sentences)."""


def _fallback_explanation(pred: dict, patient: dict) -> str:
    return (
        f"The model's {pred['confidence'] * 100:.1f}% confidence "
        f"{pred['prediction'].lower()} reading is based on the patient's "
        f"presenting profile ({', '.join(patient['symptoms'])}). Both the "
        f"primary and fallback explainability services were unavailable when "
        f"this twin was created; this is a deterministic fallback message, "
        f"not an LLM-grounded explanation."
    )
