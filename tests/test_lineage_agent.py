from backend.agents.lineage_agent import lineage_node


def test_lineage_records_expected_fields(sample_prediction):
    state = {"prediction_input": sample_prediction}
    result = lineage_node(state)

    lineage = result["lineage"]
    assert lineage["source"] == sample_prediction["model_name"]
    assert lineage["patient_id"] == sample_prediction["patient_id"]
    assert lineage["model_version"] == sample_prediction["model_version"]
    assert lineage["input_captured_at"] == sample_prediction["timestamp"]


def test_lineage_does_not_mutate_other_state_keys(sample_prediction):
    state = {"prediction_input": sample_prediction, "untouched": "value"}
    result = lineage_node(state)
    assert result["untouched"] == "value"
