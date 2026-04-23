import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.schemas.incident import Incident, Severity, IncidentStatus
from src.schemas.hypothesis import HypothesisList, Hypothesis
from src.schemas.impact import Impact, SeverityBand
from src.features.memory.memory_module import find_similar_incidents
from src.features.action.action_module import generate_actions
from src.schemas.action import ApprovalStatus, ActionType


@pytest.fixture
def sample_incident():
    return Incident(
        incident_id="test-123",
        title="Test Incident",
        service="test-service",
        severity=Severity.P1,
        started_at=datetime.utcnow(),
        detected_at=datetime.utcnow(),
        status=IncidentStatus.RUNNING,
    )


@pytest.fixture
def sample_hypotheses():
    return HypothesisList(
        hypotheses=[
            Hypothesis(
                hypothesis_id="h1",
                incident_id="test-123",
                rank=1,
                statement="DB Timeout",
                confidence_score=90,
                supporting_evidence=[],
                contradicting_evidence=[],
                missing_information=[],
            )
        ],
        analysis_confidence=90,
        is_low_confidence=False,
    )


@pytest.fixture
def sample_impact():
    return Impact(
        incident_id="test-123",
        affected_services=["test-service"],
        severity_band=SeverityBand.CRITICAL,
        probable_user_impact="Users cannot login",
    )


@pytest.mark.asyncio
@patch("src.features.memory.memory_module.vector_store")
@patch("src.features.memory.memory_module.generate")
async def test_find_similar_incidents(mock_generate, mock_vs, sample_incident, sample_hypotheses):
    mock_vs.index = MagicMock()
    mock_vs.index.ntotal = 1
    mock_vs.search_similar.return_value = [
        {"incident_id": "old-1", "similarity_score": 0.8, "text": "Old DB timeout", "previous_fix": "Restarted DB"}
    ]
    mock_generate.return_value = {"why_similar": "Both involve DB timeouts"}

    result = await find_similar_incidents(sample_incident, sample_hypotheses)
    assert len(result.matches) == 1
    assert result.matches[0].similar_to_id == "old-1"
    assert result.matches[0].why_similar == "Both involve DB timeouts"


@pytest.mark.asyncio
@patch("src.features.memory.memory_module.vector_store")
async def test_find_similar_incidents_failure_returns_empty(mock_vs, sample_incident, sample_hypotheses):
    mock_vs.index = MagicMock()
    mock_vs.index.ntotal = 1
    mock_vs.search_similar.side_effect = RuntimeError("vector store unavailable")

    result = await find_similar_incidents(sample_incident, sample_hypotheses)
    assert result.matches == []


@pytest.mark.asyncio
@patch("src.features.action.action_module.format_json")
async def test_generate_actions(mock_format_json, sample_incident, sample_impact, sample_hypotheses):
    mock_format_json.return_value = {
        "actions": [
            {
                "action_type": "jira_ticket",
                "destination": "JIRA",
                "payload_preview": "Investigate DB timeout",
                "full_payload": {"title": "DB Timeout"},
            }
        ]
    }

    result = await generate_actions(sample_incident, sample_impact, sample_hypotheses)
    assert len(result.actions) == 1
    assert result.actions[0].action_type == ActionType.JIRA_TICKET
    assert result.actions[0].approval_status == ApprovalStatus.PENDING


@pytest.mark.asyncio
@patch("src.features.action.action_module.format_json")
async def test_generate_actions_failure_returns_fallback(
    mock_format_json, sample_incident, sample_impact, sample_hypotheses
):
    mock_format_json.return_value = None

    result = await generate_actions(sample_incident, sample_impact, sample_hypotheses)
    # Now returns a fallback manual_review action instead of empty
    assert len(result.actions) == 1
    assert result.actions[0].action_type == ActionType.MANUAL_REVIEW
