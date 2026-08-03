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
