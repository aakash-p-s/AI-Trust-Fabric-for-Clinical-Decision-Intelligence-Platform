from backend.agents.twin_assembler_agent import twin_assembler_node


def test_twin_assembler_merges_all_fields():
    state = {
        "patient_id": "P0009",
        "prediction_input": {
            "patient_id": "P0009",
            "model_name": "vit-xray-pneumonia-classification",
            "model_version": "v2.1",
            "prediction": "PNEUMONIA",
            "confidence": 0.8423,
        },
        "lineage": {
            "source": "vit-xray-pneumonia-classification",
            "input_captured_at": "2026-07-31T09:11:32Z",
            "patient_id": "P0009",
            "model_version": "v2.1",
        },
        "compliance": {
            "model_version_approved": True,
            "confidence_ok": True,
            "high_risk_requires_review": True,
            "flagged": True,
            "flag_reasons": ["prediction 'PNEUMONIA' is a high-risk condition..."],
        },
        "explanation": {
            "text": "Sample explanation text.",
            "explanation_type": "narrative_llm_rag_grounded",
            "grounded_in_sources": [{"id": "kb001", "source": "CDC", "similarity_score": 0.7}],
            "low_grounding_confidence": False,
        },
    }

    result = twin_assembler_node(state)
    twin = result["twin"]

    assert twin["twin_id"]  # a UUID string was generated
    assert twin["patient_id"] == "P0009"
    assert twin["prediction"] == {"label": "PNEUMONIA", "confidence": 0.8423, "model_version": "v2.1"}
    assert twin["lineage"] == state["lineage"]
    assert twin["compliance"] == state["compliance"]
    assert twin["explanation"] == "Sample explanation text."
    assert twin["explanation_type"] == "narrative_llm_rag_grounded"
    assert twin["grounded_in_sources"] == state["explanation"]["grounded_in_sources"]
    assert twin["low_grounding_confidence"] is False
    assert twin["flagged"] is True  # denormalized from compliance.flagged
    assert twin["twin_created_at"]  # ISO timestamp string
    assert twin["review"] is None
