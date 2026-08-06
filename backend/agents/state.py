"""
backend/agents/state.py
Shared state object threaded through all four LangGraph nodes.
"""
from typing import Optional, TypedDict


class AgentState(TypedDict):
    patient_id: str
    prediction_input: dict  # raw PredictionInput as dict
    patient_context: dict  # PatientContext as dict
    rulebook: dict  # current ComplianceRulebook as dict
    lineage: Optional[dict]
    compliance: Optional[dict]
    explanation: Optional[dict]
    twin: Optional[dict]
    error: Optional[str]
    stage_durations_ms: dict  # {"lineage": 12, "compliance": 4, "explainability": 5900, "twin_assembler": 3}
