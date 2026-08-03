"""
backend/agents/explainability_agent.py
-----------------------------------------------------
The ONLY LLM-calling agent in this system.

Uses llm_explainability from backend/llm_config.py (OpenRouter, default
model openai/gpt-oss-20b:free).

RAG grounding: retrieves top_k=2 facts from the local knowledge base
(backend/services/rag_service.py) and instructs the model to use ONLY
those facts. Never uses SHAP/LIME -- the underlying diagnostic model is
a black box with no accessible internals; this is a narrative explanation,
not a mathematical feature attribution.

Structure follows the reference compliance_agent.py pattern: a dedicated
prompt builder, a retry loop, a deterministic fallback on outright failure,
and structured logging -- adapted here because this agent produces a short
prose narrative for a clinician to read, not a multi-section structured
review, so there is no REQUIRED_SECTIONS completeness check like the
reference; instead retry triggers on an empty/too-short response.
"""
import logging

from backend.agents.state import AgentState
from backend.services import rag_service

logger = logging.getLogger(__name__)

AGENT_NAME = "explainability_agent"
LOW_GROUNDING_THRESHOLD = 0.40
MAX_RETRIES = 1
MIN_RESPONSE_LENGTH = 20


def explainability_node(state: AgentState) -> AgentState:
    pred = state["prediction_input"]
    patient = state["patient_context"]

    retrieved = rag_service.retrieve(
        prediction_label=pred["prediction"],
        symptoms=patient["symptoms"],
        top_k=2,
    )
    prompt = _build_prompt(pred, patient, retrieved)

    response_text = ""
    for attempt in range(MAX_RETRIES + 1):
        try:
            from backend.llm_config import llm_explainability

            response = llm_explainability.invoke(prompt)
            response_text = (response.content or "").strip()
        except Exception as exc:  # noqa: BLE001 -- any LLM/network failure falls back
            logger.error("[%s] LLM call failed (attempt %d): %s", AGENT_NAME, attempt + 1, exc)
            response_text = _fallback_explanation(pred, patient)
            break

        if len(response_text) >= MIN_RESPONSE_LENGTH or attempt == MAX_RETRIES:
            break
        logger.warning(
            "[%s] Response too short (%d chars) -- retry %d/%d",
            AGENT_NAME, len(response_text), attempt + 1, MAX_RETRIES,
        )

    if not response_text:
        response_text = _fallback_explanation(pred, patient)

    best_score = max((r["similarity_score"] for r in retrieved), default=0.0)

    explanation = {
        "text": response_text,
        "explanation_type": "narrative_llm_rag_grounded",
        "grounded_in_sources": [
            {"id": r["id"], "source": r["source"], "similarity_score": r["similarity_score"]}
            for r in retrieved
        ],
        "low_grounding_confidence": best_score < LOW_GROUNDING_THRESHOLD,
    }
    return {**state, "explanation": explanation}


def _build_prompt(pred: dict, patient: dict, retrieved: list[dict]) -> str:
    facts_text = "\n".join(f"- {f['text']} (source: {f['source']})" for f in retrieved)
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
        f"presenting profile ({', '.join(patient['symptoms'])}). The "
        f"explainability service was unavailable when this twin was created; "
        f"this is a deterministic fallback message, not an LLM-grounded explanation."
    )
