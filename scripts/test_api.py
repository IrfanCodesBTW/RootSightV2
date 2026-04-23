"""
Proper pytest version of the manual API test script.
Uses httpx.AsyncClient with FastAPI app — no live server needed.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from src.main import app


@pytest.mark.asyncio
async def test_pipeline_via_httpx():
    """Integration test: trigger pipeline and poll for completion."""
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Trigger pipeline
        with patch("src.main.start_pipeline", new_callable=AsyncMock, return_value="test-api-123"):
            resp = await client.post("/api/trigger", json={"title": "Test via httpx", "source": "manual"})
            assert resp.status_code == 202
            data = resp.json()
            assert data["success"] is True
            incident_id = data["data"]["incident_id"]
            assert incident_id == "test-api-123"

        # Poll for status (mocked)
        sample_state = {
            "incident_id": incident_id,
            "status": "completed",
            "incident": {
                "incident_id": incident_id,
                "title": "Test via httpx",
                "service": "test-service",
                "severity": "P1",
                "started_at": "2024-05-10T14:00:00Z",
            },
            "timeline": {"events": [], "timeline_confidence": 0, "gaps_detected": 0, "total_events": 0},
            "rca": None,
            "impact": None,
            "memory": None,
            "actions": None,
            "error": None,
        }

        with patch("src.main.get_pipeline_state", return_value=sample_state):
            resp = await client.get(f"/api/incidents/{incident_id}")
            assert resp.status_code == 200
            body = resp.json()
            assert body["success"] is True
            assert body["data"]["status"] == "completed"
