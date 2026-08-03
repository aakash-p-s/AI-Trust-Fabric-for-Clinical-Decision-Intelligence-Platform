from fastapi.testclient import TestClient

from backend.db.models import DigitalTwinRow
from backend.main import app
from backend.routers.deps import get_db


def _override_get_db(db_session):
    def _get_db():
        yield db_session
    return _get_db


def _seed_twin(db_session, flagged=True, reviewed=False):
    row = DigitalTwinRow(
        patient_id="P0009",
        prediction={"label": "PNEUMONIA", "confidence": 0.84, "model_version": "v2.1"},
        lineage={"source": "x", "input_captured_at": "x", "patient_id": "P0009", "model_version": "v2.1"},
        compliance={
            "model_version_approved": True,
            "confidence_ok": True,
            "high_risk_requires_review": True,
            "flagged": flagged,
            "flag_reasons": [],
        },
        explanation="test explanation",
        explanation_type="narrative_llm_rag_grounded",
        grounded_in_sources=[],
        low_grounding_confidence=False,
        flagged=flagged,
        review=(
            {"reviewed_by": "compliance.lead", "decision": "approve", "notes": "", "reviewed_at": "2026-01-01T00:00:00+00:00"}
            if reviewed
            else None
        ),
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row


def test_list_twins_filters_by_status(db_session):
    _seed_twin(db_session, flagged=True)
    _seed_twin(db_session, flagged=False)

    app.dependency_overrides[get_db] = _override_get_db(db_session)
    try:
        client = TestClient(app)
        response = client.get("/twins", params={"status": "flagged"})
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["total"] == 1
    assert body["twins"][0]["flagged"] is True


def test_get_twin_detail_includes_patient(db_session):
    twin = _seed_twin(db_session, flagged=True)

    app.dependency_overrides[get_db] = _override_get_db(db_session)
    try:
        client = TestClient(app)
        response = client.get(f"/twins/{twin.twin_id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["patient"]["patient_id"] == "P0009"


def test_review_requires_compliance_governance_role(db_session):
    twin = _seed_twin(db_session, flagged=True)

    app.dependency_overrides[get_db] = _override_get_db(db_session)
    try:
        client = TestClient(app)
        response = client.post(
            f"/twins/{twin.twin_id}/review",
            json={"reviewer_username": "dr.mitchell", "decision": "approve", "notes": ""},
            headers={"X-User-Role": "clinician"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


def test_override_without_notes_is_rejected(db_session):
    twin = _seed_twin(db_session, flagged=True)

    app.dependency_overrides[get_db] = _override_get_db(db_session)
    try:
        client = TestClient(app)
        response = client.post(
            f"/twins/{twin.twin_id}/review",
            json={"reviewer_username": "compliance.lead", "decision": "override", "notes": ""},
            headers={"X-User-Role": "compliance_governance"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400


def test_successful_approve_review(db_session):
    twin = _seed_twin(db_session, flagged=True)

    app.dependency_overrides[get_db] = _override_get_db(db_session)
    try:
        client = TestClient(app)
        response = client.post(
            f"/twins/{twin.twin_id}/review",
            json={"reviewer_username": "compliance.lead", "decision": "approve", "notes": "Looks correct."},
            headers={"X-User-Role": "compliance_governance"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["review"]["decision"] == "approve"


def test_reviewing_twice_returns_409(db_session):
    twin = _seed_twin(db_session, flagged=True, reviewed=True)

    app.dependency_overrides[get_db] = _override_get_db(db_session)
    try:
        client = TestClient(app)
        response = client.post(
            f"/twins/{twin.twin_id}/review",
            json={"reviewer_username": "compliance.lead", "decision": "approve", "notes": ""},
            headers={"X-User-Role": "compliance_governance"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
