from fastapi.testclient import TestClient
from unittest.mock import patch

from src.main import app


client = TestClient(app, raise_server_exceptions=False)


def test_trigger_route_returns_envelope():
    with patch("rootsight.backend.main.start_pipeline", return_value="abc123"):
        response = client.post("/api/trigger", json={"bundle_file": "db_connection_pool.json"})

    assert response.status_code == 200
    assert response.json() == {
        "data": {"incident_id": "abc123", "status": "pipeline_started"},
        "error": None,
    }


def test_trigger_route_rejects_empty_payload_with_consistent_error():
    response = client.post("/api/trigger", json={})

    assert response.status_code == 422
    assert response.json() == {
        "data": None,
        "error": "Payload must be a non-empty JSON object.",
    }


def test_get_incident_route_returns_envelope():
    sample_state = {
        "incident_id": "abc123",
        "incident": {"incident_id": "abc123", "title": "Test", "service": "svc", "severity": "P1", "started_at": "2024-05-10T14:00:00Z"},
        "status": "completed",
        "timeline": {"events": [], "timeline_confidence": 0, "gaps_detected": 0, "total_events": 0, "analysis_note": None},
        "rca": None,
        "impact": None,
        "memory": None,
        "actions": None,
        "error": None,
    }

    with patch("rootsight.backend.main.get_pipeline_state", return_value=sample_state):
        response = client.get("/api/incident/abc123")

    assert response.status_code == 200
    assert response.json() == {"data": sample_state, "error": None}


def test_get_incident_route_returns_not_found_envelope():
    with patch("rootsight.backend.main.get_pipeline_state", return_value=None):
        response = client.get("/api/incident/missing")

    assert response.status_code == 404
    assert response.json() == {"data": None, "error": "Incident not found"}


def test_global_exception_handler_hides_traceback():
    with patch("rootsight.backend.main.start_pipeline", side_effect=RuntimeError("boom")):
        response = client.post("/api/trigger", json={"bundle_file": "db_connection_pool.json"})

    assert response.status_code == 500
    assert response.json()["data"] is None
    assert response.json()["error"] == "Internal server error."
