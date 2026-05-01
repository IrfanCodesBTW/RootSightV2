import pytest
from datetime import datetime
from unittest.mock import patch
from src.schemas.incident import Incident, Severity, IncidentStatus
from src.schemas.event import EventList, Event, EventType
from src.features.rca.rca_module import analyze_root_cause


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
def sample_event_list():
    return EventList(
        events=[
            Event(
                event_id="evt-1",
                incident_id="test-123",
                timestamp=datetime.utcnow(),
                event_type=EventType.TIMEOUT,
                description="Origin timeout",
                evidence_source="host-1",
                confidence=90,
            ),
            Event(
                event_id="evt-2",
                incident_id="test-123",
                timestamp=datetime.utcnow(),
                event_type=EventType.TIMEOUT,
                description="Origin timeout 2",
                evidence_source="host-1",
                confidence=90,
            ),
            Event(
                event_id="evt-3",
                incident_id="test-123",
                timestamp=datetime.utcnow(),
                event_type=EventType.TIMEOUT,
                description="Origin timeout 3",
                evidence_source="host-1",
                confidence=90,
            )
        ],
        timeline_confidence=85,
        gaps_detected=0,
        total_events=3,
    )


@pytest.mark.asyncio
async def test_analyze_root_cause_empty(sample_incident):
    empty_list = EventList(events=[], timeline_confidence=0, gaps_detected=0, total_events=0)
    result = await analyze_root_cause(empty_list, sample_incident)
    assert len(result.hypotheses) == 0
    assert result.insufficient_data is True


@pytest.mark.asyncio
@patch("src.features.rca.rca_module.generate")
async def test_analyze_root_cause_success(mock_generate, sample_event_list, sample_incident):
    mock_generate.return_value = {
        "hypotheses": [
            {
                "id": "H1",
                "text": "Service timeout due to load",
                "supporting_event_ids": ["evt-1"],
                "evidence_strength": "weak",
                "confidence": "high",
                "category": "infrastructure",
                "recommended_action_hint": "Check CPU",
            }
        ],
        "insufficient_data": False,
    }

    result = await analyze_root_cause(sample_event_list, sample_incident)
    assert len(result.hypotheses) == 1
    assert result.hypotheses[0].confidence == "high"
    assert result.insufficient_data is False


@pytest.mark.asyncio
@patch("src.features.rca.rca_module.generate")
async def test_analyze_root_cause_failure_returns_fallback(mock_generate, sample_event_list, sample_incident):
    mock_generate.side_effect = RuntimeError("gemini offline")

    result = await analyze_root_cause(sample_event_list, sample_incident)
    assert len(result.hypotheses) == 0
    assert result.insufficient_data is True
