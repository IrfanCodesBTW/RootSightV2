import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from rootsight.backend.schemas.incident import Incident, Severity, IncidentStatus
from rootsight.backend.schemas.hypothesis import HypothesisList, Hypothesis
from rootsight.backend.schemas.impact import Impact, SeverityBand
from rootsight.backend.memory_module import find_similar_incidents
from rootsight.backend.action_module import generate_actions
from rootsight.backend.schemas.action import ApprovalStatus

@pytest.fixture
def sample_incident():
    return Incident(
        incident_id="test-123",
        title="Test Incident",
        service="test-service",
        severity=Severity.P1,
        started_at=datetime.utcnow(),
        detected_at=datetime.utcnow(),
        status=IncidentStatus.ACTIVE
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
                missing_information=[]
            )
        ],
        analysis_confidence=90,
        is_low_confidence=False
    )

@pytest.fixture
def sample_impact():
    return Impact(
        incident_id="test-123",
        affected_services=["test-service"],
        severity_band=SeverityBand.CRITICAL,
        probable_user_impact="Users cannot login"
    )

@pytest.mark.asyncio
@patch("rootsight.backend.memory_module.vector_store")
@patch("rootsight.backend.memory_module.generate")
async def test_find_similar_incidents(mock_generate, mock_vs, sample_incident, sample_hypotheses):
    mock_vs.search_similar.return_value = [
        {"incident_id": "old-1", "similarity_score": 0.8, "text": "Old DB timeout", "previous_fix": "Restarted DB"}
    ]
    mock_generate.return_value = {"why_similar": "Both involve DB timeouts"}
    
    result = await find_similar_incidents(sample_incident, sample_hypotheses)
    assert len(result.matches) == 1
    assert result.matches[0].similar_to_id == "old-1"
    assert result.matches[0].why_similar == "Both involve DB timeouts"

@pytest.mark.asyncio
@patch("rootsight.backend.memory_module.vector_store")
async def test_find_similar_incidents_failure_returns_empty(mock_vs, sample_incident, sample_hypotheses):
    mock_vs.search_similar.side_effect = RuntimeError("vector store unavailable")

    result = await find_similar_incidents(sample_incident, sample_hypotheses)
    assert result.matches == []

@pytest.mark.asyncio
@patch("rootsight.backend.action_module.format_json")
async def test_generate_actions(mock_format_json, sample_incident, sample_impact, sample_hypotheses):
    mock_format_json.return_value = {
        "actions": [
            {
                "action_type": "jira_ticket",
                "destination": "JIRA",
                "payload_preview": "Investigate DB timeout",
                "full_payload": {"title": "DB Timeout"}
            }
        ]
    }
    
    result = await generate_actions(sample_incident, sample_impact, sample_hypotheses)
    assert len(result.actions) == 1
    assert result.actions[0].action_type == "jira_ticket"
    assert result.actions[0].approval_status == ApprovalStatus.PENDING

@pytest.mark.asyncio
@patch("rootsight.backend.action_module.format_json")
async def test_generate_actions_failure_returns_empty(mock_format_json, sample_incident, sample_impact, sample_hypotheses):
    mock_format_json.side_effect = RuntimeError("groq offline")

    result = await generate_actions(sample_incident, sample_impact, sample_hypotheses)
    assert result.actions == []
