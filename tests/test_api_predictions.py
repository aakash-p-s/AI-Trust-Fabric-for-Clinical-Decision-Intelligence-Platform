from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.deps import get_db


def _override_get_db(db_session):
    def _get_db():
        yield db_session
    return _get_db


@patch("backend.services.rag_service.retrieve")
def test_post_predictions_creates_twin_end_to_end(mock_retrieve, db_session, sample_prediction):
    mock_retrieve.return_value = [
        {"id": "kb001", "source": "CDC", "text": "facts", "similarity_score": 0.8}
    ]
    mock_response = MagicMock()
    mock_response.content = "A grounded explanation for testing."

    app.dependency_overrides[get_db] = _override_get_db(db_session)
    try:
        with patch("backend.llm_config.llm_explainability") as mock_llm:
            mock_llm.invoke.return_value = mock_response
            client = TestClient(app)
            response = client.post("/predictions", json=sample_prediction)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["patient_id"] == sample_prediction["patient_id"]
    assert body["prediction"]["label"] == sample_prediction["prediction"]
    assert body["flagged"] is True  # P0009 is PNEUMONIA -> always flagged
    assert body["explanation"] == "A grounded explanation for testing."
    assert body["explanation_type"] == "narrative_llm_rag_grounded"
    assert body["review"] is None


def test_post_predictions_unknown_patient_returns_404(db_session, sample_prediction):
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    try:
        bad = dict(sample_prediction)
        bad["patient_id"] = "P9999"
        client = TestClient(app)
        with patch("backend.services.rag_service.retrieve", return_value=[]):
            response = client.post("/predictions", json=bad)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_post_predictions_invalid_confidence_returns_422(db_session, sample_prediction):
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    try:
        bad = dict(sample_prediction)
        bad["confidence"] = 1.5  # out of range
        client = TestClient(app)
        response = client.post("/predictions", json=bad)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
