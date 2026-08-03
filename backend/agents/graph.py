"""
backend/agents/graph.py
Deliberately linear -- no conditional edges, no cycles. All four nodes
run every time, for every prediction, regardless of outcome, because a
Digital Compliance Twin must always contain lineage + compliance +
explanation, whether or not the prediction ends up flagged.

The only conditional logic in the whole system is downstream of this
graph: whether a completed twin also appears in the Human Review Queue
(a WHERE flagged = true filter at query time -- see backend/routers/twins.py
-- not a graph branch).

Node identifiers are suffixed with "_step" (e.g. "lineage_step") rather
than matching the AgentState field names ("lineage", "compliance", etc.)
directly. LangGraph does not allow a node name to collide with a state
key name in all versions/configurations -- this was caught during
verification when a freshly-resolved dependency set enforced the
restriction where an earlier install had not. Keeping node identifiers
and state field names distinct avoids depending on that behavior at all.
"""
from langgraph.graph import END, StateGraph

from backend.agents.compliance_agent import compliance_node
from backend.agents.explainability_agent import explainability_node
from backend.agents.lineage_agent import lineage_node
from backend.agents.state import AgentState
from backend.agents.twin_assembler_agent import twin_assembler_node


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("lineage_step", lineage_node)
    graph.add_node("compliance_step", compliance_node)
    graph.add_node("explainability_step", explainability_node)
    graph.add_node("twin_assembler_step", twin_assembler_node)

    graph.set_entry_point("lineage_step")
    graph.add_edge("lineage_step", "compliance_step")
    graph.add_edge("compliance_step", "explainability_step")
    graph.add_edge("explainability_step", "twin_assembler_step")
    graph.add_edge("twin_assembler_step", END)
    return graph.compile()


# Module-level, compiled once at import time
trust_fabric_graph = build_graph()


def run_trust_fabric_pipeline(prediction_input: dict, patient_context: dict, rulebook: dict) -> dict:
    initial_state: AgentState = {
        "patient_id": prediction_input["patient_id"],
        "prediction_input": prediction_input,
        "patient_context": patient_context,
        "rulebook": rulebook,
        "lineage": None,
        "compliance": None,
        "explanation": None,
        "twin": None,
        "error": None,
    }
    final_state = trust_fabric_graph.invoke(initial_state)
    return final_state["twin"]


def run_trust_fabric_pipeline_with_progress(
    prediction_input: dict,
    patient_context: dict,
    rulebook: dict,
    request_id: str,
) -> dict:
    """
    Identical pipeline, identical output, but uses LangGraph's .stream()
    instead of .invoke() so a progress tracker (backend/services/
    progress_service.py) can be updated after each of the 4 agents
    actually finishes -- enabling real (not simulated) per-stage progress
    in the UI via GET /predictions/stream/{request_id}/status.
    """
    from backend.services import progress_service

    initial_state: AgentState = {
        "patient_id": prediction_input["patient_id"],
        "prediction_input": prediction_input,
        "patient_context": patient_context,
        "rulebook": rulebook,
        "lineage": None,
        "compliance": None,
        "explanation": None,
        "twin": None,
        "error": None,
    }

    node_to_stage = {
        "lineage_step": "lineage",
        "compliance_step": "compliance",
        "explainability_step": "explainability",
        "twin_assembler_step": "twin_assembler",
    }

    final_twin = None
    progress_service.mark_stage_started(request_id, "lineage")

    for chunk in trust_fabric_graph.stream(initial_state):
        for node_name, updated_state in chunk.items():
            stage = node_to_stage.get(node_name)
            if stage is None:
                continue
            progress_service.mark_stage_complete(request_id, stage)

            next_stage = _next_stage_after(stage)
            if next_stage:
                progress_service.mark_stage_started(request_id, next_stage)

            if stage == "twin_assembler":
                final_twin = updated_state.get("twin")

    return final_twin


def _next_stage_after(stage: str) -> str | None:
    order = ["lineage", "compliance", "explainability", "twin_assembler"]
    idx = order.index(stage)
    return order[idx + 1] if idx + 1 < len(order) else None
