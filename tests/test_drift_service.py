from datetime import datetime, timedelta, timezone

from backend.db.models import DigitalTwinRow
from backend.services import drift_service


def _make_twin(db_session, day_offset: int, confidence: float, flagged: bool, model_version="v2.1"):
    created_at = datetime.now(timezone.utc) - timedelta(days=day_offset)
    row = DigitalTwinRow(
        patient_id="P0009",
        prediction={"label": "PNEUMONIA", "confidence": confidence, "model_version": model_version},
        lineage={"source": "x", "input_captured_at": "x", "patient_id": "P0009", "model_version": model_version},
        compliance={
            "model_version_approved": True,
            "confidence_ok": True,
            "high_risk_requires_review": True,
            "flagged": flagged,
            "flag_reasons": [],
        },
        explanation="test",
        explanation_type="narrative_llm_rag_grounded",
        grounded_in_sources=[],
        low_grounding_confidence=False,
        flagged=flagged,
        twin_created_at=created_at,
        review=None,
    )
    db_session.add(row)
    db_session.commit()
    return row


def test_confidence_drop_triggers_drift(db_session):
    _make_twin(db_session, day_offset=6, confidence=0.95, flagged=False)
    _make_twin(db_session, day_offset=0, confidence=0.70, flagged=False)  # ~26% drop

    trends = drift_service.compute_trends(db_session, model_version="v2.1")
    assert trends["confidence_drift_triggered"] is True
    assert trends["drift_status"] == "Drift Detected"


def test_stable_confidence_does_not_trigger_drift(db_session):
    _make_twin(db_session, day_offset=6, confidence=0.90, flagged=False)
    _make_twin(db_session, day_offset=0, confidence=0.89, flagged=False)

    trends = drift_service.compute_trends(db_session, model_version="v2.1")
    assert trends["confidence_drift_triggered"] is False
    assert trends["drift_status"] == "Normal"


def test_flag_rate_rise_triggers_drift(db_session):
    _make_twin(db_session, day_offset=1, confidence=0.9, flagged=False)
    _make_twin(db_session, day_offset=1, confidence=0.9, flagged=False)
    _make_twin(db_session, day_offset=0, confidence=0.9, flagged=True)
    _make_twin(db_session, day_offset=0, confidence=0.9, flagged=True)
    _make_twin(db_session, day_offset=0, confidence=0.9, flagged=True)

    trends = drift_service.compute_trends(db_session, model_version="v2.1")
    assert trends["flag_rate_drift_triggered"] is True
