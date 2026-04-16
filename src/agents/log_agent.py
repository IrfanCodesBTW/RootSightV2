"""
RootSight — Log Agent

Fetches logs from Datadog (or mock/seed data in demo mode),
normalizes them, and produces a NormalizedLogSet.
No LLM required.
"""

from __future__ import annotations
import json
from pathlib import Path

from src.schemas.incident import IncidentHeader
from src.schemas.logs import NormalizedLogSet
from src.integrations.datadog import fetch_logs
from src.services.log_normalizer import normalize_logs
from src.config import settings, SEED_DIR
from src.utils.logger import get_logger

logger = get_logger("agents.log")


def run(header: IncidentHeader, scenario_id: str = None) -> NormalizedLogSet:
    """
    Fetch and normalize logs for the incident.

    Args:
        header: Parsed incident header from Trigger Agent.
        scenario_id: Optional scenario identifier (e.g., "01", "02")
                     to load specific seed logs in demo mode.

    Returns:
        NormalizedLogSet with filtered, deduplicated logs.
    """
    logger.info(f"Log Agent — fetching logs for {header.service} around {header.timestamp}")

    raw_logs = []

    if settings.DEMO_MODE and scenario_id:
        # Load scenario-specific seed logs
        seed_file = SEED_DIR / "sample_logs" / f"demo_logs_{scenario_id}.json"
        if seed_file.exists():
            with open(seed_file) as f:
                data = json.load(f)
                raw_logs = data.get("logs", data) if isinstance(data, dict) else data
                logger.info(f"Loaded {len(raw_logs)} seed log entries from {seed_file.name}")
        else:
            logger.warning(f"Seed log file not found: {seed_file}, falling back to API")
            raw_logs = fetch_logs(header.service, header.timestamp)
    else:
        raw_logs = fetch_logs(
            service=header.service,
            alert_time=header.timestamp,
            window_minutes=settings.LOG_TIME_WINDOW_MINUTES,
        )

    if not raw_logs:
        logger.warning("No logs retrieved — producing empty log set")

    log_set = normalize_logs(
        incident_id=header.incident_id,
        raw_logs=raw_logs,
        alert_time=header.timestamp,
        window_minutes=settings.LOG_TIME_WINDOW_MINUTES,
    )

    logger.info(
        f"Log Agent — complete: {log_set.total_raw_count} raw → "
        f"{log_set.filtered_count} filtered "
        f"(quality: {log_set.data_quality.completeness})"
    )
    return log_set
