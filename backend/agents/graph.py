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

Per-stage timing: every node is wrapped by _timed() below, which records
wall-clock duration into state["stage_durations_ms"] under the stage's
friendly name. This is generic -- individual agent files never need
their own timing code.
"""
import time

from langgraph.graph import END, StateGraph

from backend.agents.compliance_agent import compliance_node
from backend.agents.explainability_agent import explainability_node
from backend.agents.lineage_agent import lineage_node
from backend.agents.state import AgentState
from backend.agents.twin_assembler_agent import twin_assembler_node

NODE_TO_STAGE = {
    "lineage_step": "lineage",
    "compliance_step": "compliance",
    "explainability_step": "explainability",
    "twin_assembler_step": "twin_assembler",
}


def _timed(stage_name: str, node_fn):
    def wrapped(state: AgentState) -> AgentState:
        started = time.monotonic()
        new_state = node_fn(state)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        durations = dict(new_state.get("stage_durations_ms") or {})
        durations[stage_name] = elapsed_ms
        return {**new_state, "stage_durations_ms": durations}

    return wrapped


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("lineage_step", _timed("lineage", lineage_node))
    graph.add_node("compliance_step", _timed("compliance", compliance_node))
    graph.add_node("explainability_step", _timed("explainability", explainability_node))
    graph.add_node("twin_assembler_step", _timed("twin_assembler", twin_assembler_node))

    graph.set_entry_point("lineage_step")
    graph.add_edge("lineage_step", "compliance_step")
    graph.add_edge("compliance_step", "explainability_step")
    graph.add_edge("explainability_step", "twin_assembler_step")
    graph.add_edge("twin_assembler_step", END)
    return graph.compile()


# Module-level, compiled once at import time
trust_fabric_graph = build_graph()


def _initial_state(prediction_input: dict, patient_context: dict, rulebook: dict) -> AgentState:
    return {
        "patient_id": prediction_input["patient_id"],
        "prediction_input": prediction_input,
        "patient_context": patient_context,
        "rulebook": rulebook,
        "lineage": None,
        "compliance": None,
        "explanation": None,
        "twin": None,
        "error": None,
        "stage_durations_ms": {},
    }


def run_trust_fabric_pipeline(prediction_input: dict, patient_context: dict, rulebook: dict) -> dict:
    initial_state = _initial_state(prediction_input, patient_context, rulebook)
    final_state = trust_fabric_graph.invoke(initial_state)
    twin = final_state["twin"]
    twin["stage_durations_ms"] = final_state.get("stage_durations_ms", {})
    return twin


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

    initial_state = _initial_state(prediction_input, patient_context, rulebook)

    final_twin = None
    final_durations = {}
    progress_service.mark_stage_started(request_id, "lineage")

    for chunk in trust_fabric_graph.stream(initial_state):
        for node_name, updated_state in chunk.items():
            stage = NODE_TO_STAGE.get(node_name)
            if stage is None:
                continue
            progress_service.mark_stage_complete(request_id, stage)

            next_stage = _next_stage_after(stage)
            if next_stage:
                progress_service.mark_stage_started(request_id, next_stage)

            if stage == "twin_assembler":
                final_twin = updated_state.get("twin")
                final_durations = updated_state.get("stage_durations_ms", {})

    if final_twin is not None:
        final_twin["stage_durations_ms"] = final_durations
    return final_twin


def _next_stage_after(stage: str) -> str | None:
    order = ["lineage", "compliance", "explainability", "twin_assembler"]
    idx = order.index(stage)
    return order[idx + 1] if idx + 1 < len(order) else None
