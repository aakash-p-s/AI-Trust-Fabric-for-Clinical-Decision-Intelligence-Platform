import time
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.deps import get_db


def _override_get_db(db_session):
    def _get_db():
        yield db_session
    return _get_db


@patch("backend.services.rag_service.retrieve")
def test_stream_endpoint_progresses_through_all_four_stages(mock_retrieve, db_session, sample_prediction):
    mock_retrieve.return_value = [
        {"id": "kb001", "source": "CDC", "text": "facts", "similarity_score": 0.8}
    ]
    mock_response = MagicMock()
    mock_response.content = "A grounded explanation for the streaming test."

    app.dependency_overrides[get_db] = _override_get_db(db_session)
    try:
        with patch("backend.llm_config.llm_explainability") as mock_llm:
            mock_llm.invoke.return_value = mock_response
            client = TestClient(app)

            start_response = client.post("/predictions/stream", json=sample_prediction)
            assert start_response.status_code == 202
            request_id = start_response.json()["request_id"]

            # Poll until done, with a generous timeout since this runs on a
            # background thread started by TestClient's own app instance.
            final_status = None
            for _ in range(100):
                status_response = client.get(f"/predictions/stream/{request_id}/status")
                assert status_response.status_code == 200
                body = status_response.json()
                if body["done"]:
                    final_status = body
                    break
                time.sleep(0.05)
    finally:
        app.dependency_overrides.clear()

    assert final_status is not None, "pipeline never reported done within the polling window"
    assert final_status["error"] is None
    assert set(final_status["completed_stages"]) == {
        "lineage", "compliance", "explainability", "twin_assembler"
    }
    assert final_status["twin"]["patient_id"] == sample_prediction["patient_id"]
    assert final_status["twin"]["explanation"] == "A grounded explanation for the streaming test."


def test_status_endpoint_returns_404_for_unknown_request_id():
    client = TestClient(app)
    response = client.get("/predictions/stream/not-a-real-id/status")
    assert response.status_code == 404


def test_stream_endpoint_404_for_unknown_patient(db_session, sample_prediction):
    app.dependency_overrides[get_db] = _override_get_db(db_session)
    try:
        bad = dict(sample_prediction)
        bad["patient_id"] = "P9999"
        client = TestClient(app)
        response = client.post("/predictions/stream", json=bad)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
