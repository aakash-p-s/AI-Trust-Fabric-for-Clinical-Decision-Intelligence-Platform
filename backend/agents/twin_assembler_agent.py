"""
backend/agents/twin_assembler_agent.py
Deterministic merge. No LLM. Generates the twin_id and merges lineage +
compliance + explanation into the final Digital Compliance Twin record.
"""
import uuid
from datetime import datetime, timezone

from backend.agents.state import AgentState

AGENT_NAME = "twin_assembler_agent"


def twin_assembler_node(state: AgentState) -> AgentState:
    pred = state["prediction_input"]
    exp = state["explanation"]

    twin = {
        "twin_id": str(uuid.uuid4()),
        "patient_id": state["patient_id"],
        "prediction": {
            "label": pred["prediction"],
            "confidence": pred["confidence"],
            "model_version": pred["model_version"],
        },
        "lineage": state["lineage"],
        "compliance": state["compliance"],
        "explanation": exp["text"],
        "explanation_type": exp["explanation_type"],
        "grounded_in_sources": exp["grounded_in_sources"],
        "low_grounding_confidence": exp["low_grounding_confidence"],
        "explanation_cascade": exp.get("cascade"),
        "rag_details": exp.get("rag"),
        "flagged": state["compliance"]["flagged"],
        "twin_created_at": datetime.now(timezone.utc).isoformat(),
        "review": None,
    }
    return {**state, "twin": twin}
