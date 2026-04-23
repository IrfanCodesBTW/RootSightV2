import pytest
from datetime import datetime
from unittest.mock import patch
from src.schemas.incident import Incident, Severity, IncidentStatus
from src.features.ingestion.ingestion_service import RawEvent
from src.features.timeline.timeline_module import build_timeline
from src.schemas.event import EventType


@pytest.fixture
def sample_incident():
    return Incident(
        incident_id="test-123",
        title="Test Incident",
        service="test-service",
        severity=Severity.P1,
        environment="production",
        region="us-east-1",
        source="pagerduty",
        started_at=datetime.utcnow(),
        detected_at=datetime.utcnow(),
        status=IncidentStatus.RUNNING,
    )


@pytest.fixture
def sample_raw_events():
    return [
        RawEvent(
            timestamp="2024-05-10T14:00:05Z",
            level="WARN",
            message="CPU utilization exceeded 80%",
            source="host-1",
            service="test-service",
        ),
        RawEvent(
            timestamp="2024-05-10T14:00:15Z",
            level="ERROR",
            message="Origin timeout waiting for connection",
            source="host-1",
            service="test-service",
        ),
    ]


@pytest.mark.asyncio
async def test_build_timeline_empty(sample_incident):
    result = await build_timeline([], sample_incident)
    # Now returns a synthetic event as fallback
    assert len(result.events) == 1
    assert result.events[0].event_type == EventType.UNKNOWN
    assert result.timeline_confidence == 0
    assert "No logs ingested" in result.analysis_note


@pytest.mark.asyncio
@patch("src.features.timeline.timeline_module.generate")
async def test_build_timeline_success(mock_generate, sample_incident, sample_raw_events):
    mock_generate.return_value = {
        "events": [
            {
                "timestamp": "2024-05-10T14:00:15Z",
                "event_type": "timeout",
                "description": "Origin timeout waiting for connection",
                "evidence_source": "host-1",
                "confidence": 90,
            }
        ],
        "timeline_confidence": 85,
        "gaps_detected": 0,
    }

    result = await build_timeline(sample_raw_events, sample_incident)
    assert len(result.events) == 1
    assert result.events[0].event_type == EventType.TIMEOUT
    assert result.events[0].confidence == 90
    assert result.timeline_confidence == 85
    assert result.gaps_detected == 0


@pytest.mark.asyncio
@patch("src.features.timeline.timeline_module.generate")
async def test_build_timeline_failure_returns_fallback(mock_generate, sample_incident, sample_raw_events):
    mock_generate.side_effect = RuntimeError("gemini offline")

    result = await build_timeline(sample_raw_events, sample_incident)
    # Fallback now includes a synthetic event
    assert len(result.events) == 1
    assert result.timeline_confidence == 0
    assert "LLM failure" in result.analysis_note
