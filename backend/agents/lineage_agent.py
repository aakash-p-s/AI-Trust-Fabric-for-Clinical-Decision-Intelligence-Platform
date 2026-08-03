"""
backend/agents/lineage_agent.py
Deterministic. No LLM. Records provenance only: which patient data and
model version produced this specific prediction.
"""
from backend.agents.state import AgentState

AGENT_NAME = "lineage_agent"


def lineage_node(state: AgentState) -> AgentState:
    pred = state["prediction_input"]

    lineage = {
        "source": pred["model_name"],
        "input_captured_at": _as_iso(pred["timestamp"]),
        "patient_id": pred["patient_id"],
        "model_version": pred["model_version"],
    }
    return {**state, "lineage": lineage}


def _as_iso(value) -> str:
    """timestamp may arrive as a datetime object or an already-serialized string."""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
