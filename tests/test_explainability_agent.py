from unittest.mock import MagicMock, patch

from backend.agents.explainability_agent import explainability_node, _fallback_explanation


def _fake_retrieved():
    return [
        {"id": "kb001", "source": "CDC", "text": "Pneumonia facts...", "similarity_score": 0.81},
        {"id": "kb002", "source": "CDC", "text": "More facts...", "similarity_score": 0.55},
    ]


def _base_state():
    return {
        "prediction_input": {
            "patient_id": "P0009",
            "model_name": "vit-xray-pneumonia-classification",
            "model_version": "v2.1",
            "prediction": "PNEUMONIA",
            "confidence": 0.8423,
        },
        "patient_context": {
            "patient_id": "P0009",
            "age": 64,
            "symptoms": ["low oxygen saturation", "cough"],
            "scan_type": "chest_xray",
            "relevant_history": "smoker, prior respiratory issues",
        },
    }


@patch("backend.services.rag_service.retrieve")
def test_explanation_is_grounded_and_uses_llm_response(mock_retrieve):
    mock_retrieve.return_value = _fake_retrieved()

    mock_response = MagicMock()
    mock_response.content = "The prediction aligns with known pneumonia risk factors."

    with patch("backend.llm_config.llm_explainability") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = explainability_node(_base_state())

    exp = result["explanation"]
    assert exp["text"] == "The prediction aligns with known pneumonia risk factors."
    assert exp["explanation_type"] == "narrative_llm_rag_grounded"
    assert len(exp["grounded_in_sources"]) == 2
    assert exp["grounded_in_sources"][0]["id"] == "kb001"
    assert exp["low_grounding_confidence"] is False  # best score 0.81 >= 0.40


@patch("backend.services.rag_service.retrieve")
def test_low_grounding_confidence_flag_set_below_threshold(mock_retrieve):
    mock_retrieve.return_value = [
        {"id": "kb003", "source": "X", "text": "weak match", "similarity_score": 0.20}
    ]
    mock_response = MagicMock()
    mock_response.content = "A weakly grounded explanation."

    with patch("backend.llm_config.llm_explainability") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = explainability_node(_base_state())

    assert result["explanation"]["low_grounding_confidence"] is True


@patch("backend.services.rag_service.retrieve")
def test_llm_failure_falls_back_to_deterministic_message(mock_retrieve):
    mock_retrieve.return_value = _fake_retrieved()

    with patch("backend.llm_config.llm_explainability") as mock_llm:
        mock_llm.invoke.side_effect = Exception("network error")
        result = explainability_node(_base_state())

    exp = result["explanation"]
    assert "explainability service was unavailable" in exp["text"]
    assert exp["explanation_type"] == "narrative_llm_rag_grounded"


def test_fallback_explanation_mentions_prediction_and_confidence():
    pred = {"prediction": "PNEUMONIA", "confidence": 0.84}
    patient = {"symptoms": ["cough"]}
    text = _fallback_explanation(pred, patient)
    assert "84.0%" in text
    assert "pneumonia" in text.lower()
