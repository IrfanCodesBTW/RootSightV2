"""
Tests for RCA evidence anchoring:
  - Valid citations → schema passes
  - Empty supporting_event_ids → retry triggered
  - Second failure → fallback returned
"""
import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock
from pydantic import ValidationError

from src.schemas.incident import Incident, Severity, IncidentStatus
from src.schemas.event import EventList, Event, EventType
from src.schemas.hypothesis import Hypothesis, HypothesisList
from src.features.rca.rca_module import analyze_root_cause, _fallback_hypothesis


# ── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_incident():
    return Incident(
        incident_id="test-evidence-001",
        title="CDN 502 Storm",
        service="content-delivery",
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
    """3 events — enough to trigger RCA analysis."""
    return EventList(
        events=[
            Event(
                event_id="E1",
                incident_id="test-evidence-001",
                timestamp=datetime.utcnow(),
                event_type=EventType.DEPLOY,
                description="Deployment v2.4.1 pushed",
                evidence_source="deploy-bot",
                confidence=95,
            ),
            Event(
                event_id="E2",
                incident_id="test-evidence-001",
                timestamp=datetime.utcnow(),
                event_type=EventType.LATENCY_SPIKE,
                description="p99 latency spiked to 1200ms",
                evidence_source="datadog-metrics",
                confidence=88,
            ),
            Event(
                event_id="E3",
                incident_id="test-evidence-001",
                timestamp=datetime.utcnow(),
                event_type=EventType.ERROR_SPIKE,
                description="502 error rate exceeded 15%",
                evidence_source="cdn-logs",
                confidence=92,
            ),
        ],
        timeline_confidence=85,
        gaps_detected=0,
        total_events=3,
    )


@pytest.fixture
def valid_rca_response():
    """A valid LLM response with proper evidence anchoring."""
    return {
        "hypotheses": [
            {
                "id": "H1",
                "text": "Deployment v2.4.1 introduced a regression causing 502 errors",
                "supporting_event_ids": ["E1", "E3"],
                "evidence_strength": "moderate",
                "confidence": "high",
                "category": "application",
                "recommended_action_hint": "Rollback to v2.3.9 and compare error rates",
            },
            {
                "id": "H2",
                "text": "CDN cache invalidation overwhelmed origin servers",
                "supporting_event_ids": ["E2", "E3"],
                "evidence_strength": "moderate",
                "confidence": "medium",
                "category": "infrastructure",
                "recommended_action_hint": "Check CDN purge logs and origin autoscaling",
            },
        ],
        "insufficient_data": False,
    }


# ── Schema Tests ────────────────────────────────────────────────────────────────


class TestHypothesisSchema:
    """Direct Pydantic schema validation tests."""

    def test_valid_hypothesis_with_evidence(self):
        """Valid citations → schema passes."""
        h = Hypothesis(
            id="H1",
            text="Service timeout due to load",
            supporting_event_ids=["E1", "E2"],
            evidence_strength="strong",
            confidence="high",
            category="infrastructure",
            recommended_action_hint="Check CPU utilization",
        )
        assert h.supporting_event_ids == ["E1", "E2"]
        assert h.evidence_strength == "strong"
        assert h.category == "infrastructure"

    def test_empty_supporting_event_ids_rejected(self):
        """Empty supporting_event_ids → ValidationError (min_length=1)."""
        with pytest.raises(ValidationError) as exc_info:
            Hypothesis(
                id="H1",
                text="Some hypothesis",
                supporting_event_ids=[],
                evidence_strength="weak",
                confidence="low",
                category="application",
                recommended_action_hint="Investigate",
            )
        errors = exc_info.value.errors()
        assert any("supporting_event_ids" in str(e) for e in errors)

    def test_evidence_strength_default_is_weak(self):
        """evidence_strength defaults to 'weak' when not provided."""
        h = Hypothesis(
            id="H1",
            text="Some hypothesis",
            supporting_event_ids=["E1"],
            confidence="low",
            category="application",
            recommended_action_hint="Investigate",
        )
        assert h.evidence_strength == "weak"

    def test_evidence_strength_invalid_value_rejected(self):
        """Invalid evidence_strength value → ValidationError."""
        with pytest.raises(ValidationError):
            Hypothesis(
                id="H1",
                text="Some hypothesis",
                supporting_event_ids=["E1"],
                evidence_strength="super_strong",
                confidence="low",
                category="application",
                recommended_action_hint="Investigate",
            )

    def test_invalid_category_rejected(self):
        """Invalid category value → ValidationError."""
        with pytest.raises(ValidationError):
            Hypothesis(
                id="H1",
                text="Some hypothesis",
                supporting_event_ids=["E1"],
                evidence_strength="weak",
                confidence="low",
                category="networking",
                recommended_action_hint="Investigate",
            )

    def test_hypothesis_list_with_valid_evidence(self):
        """HypothesisList accepts hypotheses with proper evidence anchoring."""
        result = HypothesisList(
            hypotheses=[
                Hypothesis(
                    id="H1",
                    text="Root cause A",
                    supporting_event_ids=["E1", "E2", "E3"],
                    evidence_strength="strong",
                    confidence="high",
                    category="infrastructure",
                    recommended_action_hint="Scale up",
                ),
            ],
            insufficient_data=False,
        )
        assert len(result.hypotheses) == 1
        assert result.hypotheses[0].evidence_strength == "strong"


# ── Integration Tests (mocked LLM) ─────────────────────────────────────────────


class TestAnalyzeRootCause:
    """Tests for the analyze_root_cause function with mocked LLM calls."""

    @pytest.mark.asyncio
    @patch("src.features.rca.rca_module.generate")
    async def test_valid_citations_pass(self, mock_generate, sample_event_list, sample_incident, valid_rca_response):
        """Valid citations → schema passes, returns hypotheses."""
        mock_generate.return_value = valid_rca_response

        result = await analyze_root_cause(sample_event_list, sample_incident)

        assert len(result.hypotheses) == 2
        assert result.hypotheses[0].supporting_event_ids == ["E1", "E3"]
        assert result.hypotheses[0].evidence_strength == "moderate"
        assert result.hypotheses[0].category == "application"
        assert result.insufficient_data is False
        mock_generate.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.features.rca.rca_module.generate")
    async def test_empty_event_ids_triggers_retry(self, mock_generate, sample_event_list, sample_incident, valid_rca_response):
        """Empty supporting_event_ids on first attempt → retry triggered with stricter prompt."""
        # First call: invalid response (empty supporting_event_ids)
        invalid_response = {
            "hypotheses": [
                {
                    "id": "H1",
                    "text": "Bad hypothesis",
                    "supporting_event_ids": [],
                    "evidence_strength": "weak",
                    "confidence": "low",
                    "category": "application",
                    "recommended_action_hint": "N/A",
                }
            ],
            "insufficient_data": False,
        }
        # Second call: valid response
        mock_generate.side_effect = [invalid_response, valid_rca_response]

        result = await analyze_root_cause(sample_event_list, sample_incident)

        # Should have retried and succeeded
        assert mock_generate.call_count == 2
        assert len(result.hypotheses) == 2
        assert result.hypotheses[0].supporting_event_ids == ["E1", "E3"]

    @pytest.mark.asyncio
    @patch("src.features.rca.rca_module.generate")
    async def test_second_failure_returns_fallback(self, mock_generate, sample_event_list, sample_incident):
        """Both attempts fail validation → fallback returned."""
        invalid_response = {
            "hypotheses": [
                {
                    "id": "H1",
                    "text": "Bad hypothesis",
                    "supporting_event_ids": [],
                    "evidence_strength": "weak",
                    "confidence": "low",
                    "category": "application",
                    "recommended_action_hint": "N/A",
                }
            ],
            "insufficient_data": False,
        }
        # Both calls return invalid data
        mock_generate.side_effect = [invalid_response, invalid_response]

        result = await analyze_root_cause(sample_event_list, sample_incident)

        assert mock_generate.call_count == 2
        assert len(result.hypotheses) == 0
        assert result.insufficient_data is True

    @pytest.mark.asyncio
    @patch("src.features.rca.rca_module.generate")
    async def test_llm_exception_triggers_retry(self, mock_generate, sample_event_list, sample_incident, valid_rca_response):
        """LLM exception on first attempt → retry, second succeeds."""
        mock_generate.side_effect = [RuntimeError("Gemini 503"), valid_rca_response]

        result = await analyze_root_cause(sample_event_list, sample_incident)

        assert mock_generate.call_count == 2
        assert len(result.hypotheses) == 2

    @pytest.mark.asyncio
    @patch("src.features.rca.rca_module.generate")
    async def test_both_llm_exceptions_return_fallback(self, mock_generate, sample_event_list, sample_incident):
        """Both LLM attempts throw exceptions → fallback."""
        mock_generate.side_effect = [RuntimeError("Gemini 503"), RuntimeError("Gemini 429")]

        result = await analyze_root_cause(sample_event_list, sample_incident)

        assert mock_generate.call_count == 2
        assert len(result.hypotheses) == 0
        assert result.insufficient_data is True

    @pytest.mark.asyncio
    async def test_insufficient_events_returns_fallback(self, sample_incident):
        """Fewer than 3 events → immediate fallback without calling LLM."""
        few_events = EventList(
            events=[
                Event(
                    event_id="E1",
                    incident_id="test-evidence-001",
                    timestamp=datetime.utcnow(),
                    event_type=EventType.TIMEOUT,
                    description="Timeout",
                    evidence_source="host",
                    confidence=90,
                ),
            ],
            timeline_confidence=50,
            gaps_detected=0,
            total_events=1,
        )

        result = await analyze_root_cause(few_events, sample_incident)
        assert len(result.hypotheses) == 0
        assert result.insufficient_data is True


class TestFallbackHypothesis:
    """Tests for the _fallback_hypothesis helper."""

    def test_fallback_returns_empty_list(self):
        result = _fallback_hypothesis("test note")
        assert len(result.hypotheses) == 0
        assert result.insufficient_data is True

    def test_fallback_schema_valid(self):
        result = _fallback_hypothesis("Manual investigation required.")
        # Should be valid HypothesisList
        assert isinstance(result, HypothesisList)
        assert result.insufficient_data is True
