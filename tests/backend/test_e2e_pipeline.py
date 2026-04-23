import pytest
import asyncio
import json
from unittest.mock import patch
from src.features.orchestrator.pipeline_orchestrator import start_pipeline, get_pipeline_state
from src.schemas.incident import IncidentStatus


@pytest.mark.asyncio
@patch("src.features.timeline.timeline_module.generate")
@patch("src.features.rca.rca_module.generate")
@patch("src.features.impact.impact_module.generate")
@patch("src.features.memory.memory_module.generate")
@patch("src.features.memory.memory_module.vector_store")
@patch("src.features.action.action_module.format_json")
async def test_end_to_end_pipeline(
    mock_format_json,
    mock_vector_store,
    mock_generate_memory,
    mock_generate_impact,
    mock_generate_rca,
    mock_generate_timeline,
):
    # Mock all external LLM / FAISS calls
    mock_generate_timeline.return_value = {
        "events": [
            {
                "timestamp": "2024-05-10T14:00:15Z",
                "event_type": "timeout",
                "description": "Origin timeout",
                "evidence_source": "host-1",
                "confidence": 90,
            }
        ],
        "timeline_confidence": 85,
        "gaps_detected": 0,
    }

    mock_generate_rca.return_value = {
        "hypotheses": [
            {
                "rank": 1,
                "statement": "Service timeout due to load",
                "confidence_score": 85,
                "supporting_evidence": ["timeout log"],
                "contradicting_evidence": [],
                "missing_information": [],
                "recommended_check": "Check CPU",
            }
        ],
        "analysis_confidence": 80,
        "is_low_confidence": False,
    }

    mock_generate_impact.return_value = {
        "affected_services": ["content-delivery"],
        "severity_band": "high",
        "probable_user_impact": "Users experience latency",
        "business_impact_summary": "High latency",
    }

    mock_vector_store.index = None  # Disable vector store for tests
    mock_vector_store.search_similar.return_value = []

    mock_format_json.return_value = {
        "actions": [
            {
                "action_type": "jira_ticket",
                "destination": "JIRA",
                "payload_preview": "Investigate timeout",
                "full_payload": {"title": "Timeout"},
            }
        ]
    }

    # Start pipeline with the CDN mock bundle
    payload = {"bundle_file": "cdn_502_incident.json"}
    incident_id = await start_pipeline(payload)

    # Wait a bit for the async task to complete
    await asyncio.sleep(1.0)

    state = get_pipeline_state(incident_id)
    assert state is not None
    status = state["status"]

    # Status uses IncidentStatus enum values (lowercase strings)
    if status not in (IncidentStatus.COMPLETED, IncidentStatus.PARTIAL, IncidentStatus.DEGRADED):
        print(f"DEBUG: Pipeline failed with state: {json.dumps(state, indent=2, default=str)}")

    assert status in (IncidentStatus.COMPLETED, IncidentStatus.PARTIAL, IncidentStatus.DEGRADED)
    assert state["timeline"] is not None
    assert state["rca"] is not None
