from backend.agents.compliance_agent import compliance_node


def test_approved_version_high_confidence_high_risk_condition_is_flagged(rulebook_dict):
    """PNEUMONIA is always flagged regardless of confidence or version, per the
    high_risk_conditions_requiring_review rule (PRD Section 15.1)."""
    pred = {
        "patient_id": "X",
        "model_name": "vit-xray-pneumonia-classification",
        "model_version": "v2.1",
        "prediction": "PNEUMONIA",
        "confidence": 0.99,
    }
    result = compliance_node({"prediction_input": pred, "rulebook": rulebook_dict})
    c = result["compliance"]
    assert c["model_version_approved"] is True
    assert c["confidence_ok"] is True
    assert c["high_risk_requires_review"] is True
    assert c["flagged"] is True


def test_normal_high_confidence_approved_version_is_not_flagged(rulebook_dict):
    pred = {
        "patient_id": "X",
        "model_name": "vit-xray-pneumonia-classification",
        "model_version": "v2.1",
        "prediction": "NORMAL",
        "confidence": 0.95,
    }
    result = compliance_node({"prediction_input": pred, "rulebook": rulebook_dict})
    c = result["compliance"]
    assert c["flagged"] is False
    assert c["flag_reasons"] == []


def test_unapproved_version_is_flagged_with_reason(rulebook_dict):
    pred = {
        "patient_id": "X",
        "model_name": "vit-xray-pneumonia-classification",
        "model_version": "v1.9",
        "prediction": "NORMAL",
        "confidence": 0.95,
    }
    result = compliance_node({"prediction_input": pred, "rulebook": rulebook_dict})
    c = result["compliance"]
    assert c["model_version_approved"] is False
    assert c["flagged"] is True
    assert any("not in approved list" in r for r in c["flag_reasons"])


def test_low_confidence_is_flagged_with_reason(rulebook_dict):
    pred = {
        "patient_id": "X",
        "model_name": "vit-xray-pneumonia-classification",
        "model_version": "v2.1",
        "prediction": "NORMAL",
        "confidence": 0.50,
    }
    result = compliance_node({"prediction_input": pred, "rulebook": rulebook_dict})
    c = result["compliance"]
    assert c["confidence_ok"] is False
    assert c["flagged"] is True
    assert any("below threshold" in r for r in c["flag_reasons"])


def test_confidence_exactly_at_threshold_is_ok(rulebook_dict):
    """Boundary case: confidence == threshold should pass (>=, not >)."""
    pred = {
        "patient_id": "X",
        "model_name": "vit-xray-pneumonia-classification",
        "model_version": "v2.1",
        "prediction": "NORMAL",
        "confidence": rulebook_dict["minimum_confidence_threshold"],
    }
    result = compliance_node({"prediction_input": pred, "rulebook": rulebook_dict})
    assert result["compliance"]["confidence_ok"] is True


def test_prediction_label_case_insensitive_against_rulebook(rulebook_dict):
    """Regression test for the case-sensitivity bug found during manual
    verification: predictions.json uses 'PNEUMONIA' (all caps), while
    compliance_rulebook.json uses 'Pneumonia' (title case). These must match."""
    pred = {
        "patient_id": "X",
        "model_name": "vit-xray-pneumonia-classification",
        "model_version": "v2.1",
        "prediction": "PNEUMONIA",
        "confidence": 0.99,
    }
    result = compliance_node({"prediction_input": pred, "rulebook": rulebook_dict})
    assert result["compliance"]["high_risk_requires_review"] is True


def test_all_three_reasons_can_appear_together(rulebook_dict):
    pred = {
        "patient_id": "X",
        "model_name": "vit-xray-pneumonia-classification",
        "model_version": "v1.9",
        "prediction": "PNEUMONIA",
        "confidence": 0.10,
    }
    result = compliance_node({"prediction_input": pred, "rulebook": rulebook_dict})
    c = result["compliance"]
    assert c["flagged"] is True
    assert len(c["flag_reasons"]) == 3


def test_seed_data_matches_known_reference_flag_count(rulebook_dict):
    """The full 60-record seed set must produce exactly 24 flagged twins,
    matching the project's known reference human_review_queue.json."""
    import json
    from pathlib import Path

    data_dir = Path(__file__).resolve().parents[1] / "data"
    with open(data_dir / "predictions.json") as f:
        predictions = json.load(f)

    flagged_ids = []
    for p in predictions:
        result = compliance_node({"prediction_input": p, "rulebook": rulebook_dict})
        if result["compliance"]["flagged"]:
            flagged_ids.append(p["patient_id"])

    assert len(flagged_ids) == 24
