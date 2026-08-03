"""
backend/agents/compliance_agent.py
-----------------------------------------------------
Deterministic rule engine. No LLM.

Unlike the reference example's compliance agent (which used an LLM --
llm_fast -- for a regulatory-narrative style review), THIS system's
Compliance Agent is pure rule-matching by design: compliance pass/fail
must be reproducible and auditable, and must never vary between two runs
of the same input. See PRD Section 11.3.b for the rationale.

Checks three independent rules against the current rulebook and records
ALL failing reasons, not just the first one found, so Compliance/
Governance sees the full picture (PRD Section 15.1).
"""
from backend.agents.state import AgentState

AGENT_NAME = "compliance_agent"


def compliance_node(state: AgentState) -> AgentState:
    pred = state["prediction_input"]
    rulebook = state["rulebook"]
    reasons: list[str] = []

    version_ok = pred["model_version"] in rulebook["approved_model_versions"]
    if not version_ok:
        reasons.append(
            f"model_version '{pred['model_version']}' not in approved list "
            f"{rulebook['approved_model_versions']}"
        )

    confidence_ok = pred["confidence"] >= rulebook["minimum_confidence_threshold"]
    if not confidence_ok:
        reasons.append(
            f"confidence {pred['confidence']} below threshold "
            f"{rulebook['minimum_confidence_threshold']}"
        )

    high_risk_conditions_upper = {c.upper() for c in rulebook["high_risk_conditions_requiring_review"]}
    high_risk = pred["prediction"].upper() in high_risk_conditions_upper
    if high_risk:
        reasons.append(
            f"prediction '{pred['prediction']}' is a high-risk condition "
            "requiring human review regardless of confidence"
        )

    flagged = (not version_ok) or (not confidence_ok) or high_risk

    compliance = {
        "model_version_approved": version_ok,
        "confidence_ok": confidence_ok,
        "high_risk_requires_review": high_risk,
        "flagged": flagged,
        "flag_reasons": reasons,
    }
    return {**state, "compliance": compliance}
