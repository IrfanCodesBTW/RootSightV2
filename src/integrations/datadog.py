"""
RootSight — Datadog Integration

Fetches logs from Datadog's Log Search API.
Falls back to mock data in demo mode.
"""

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

import httpx

from src.config import settings, MOCK_DIR, SEED_DIR
from src.utils.logger import get_logger

logger = get_logger("integrations.datadog")

DATADOG_LOGS_URL = f"https://api.{settings.DATADOG_SITE}/api/v2/logs/events/search"


def fetch_logs(
    service: str,
    alert_time: str,
    window_minutes: int = 30,
) -> list[dict]:
    """
    Fetch logs for a service around the alert time.

    In demo mode, loads from seed/mock data.
    In real mode, queries Datadog API.

    Args:
        service: Service name to query logs for.
        alert_time: ISO-8601 timestamp of the alert.
        window_minutes: Time window ± from alert time.

    Returns:
        List of raw log entries (dicts).
    """
    if settings.DEMO_MODE:
        return _load_mock_logs(service)

    return _fetch_real_logs(service, alert_time, window_minutes)


def _load_mock_logs(service: str) -> list[dict]:
    """Load mock logs from seed or mock directories."""
    # Try service-specific seed data first
    seed_files = list((SEED_DIR / "sample_logs").glob("*.json")) if (SEED_DIR / "sample_logs").exists() else []
    for f in seed_files:
        with open(f) as fh:
            data = json.load(fh)
            if isinstance(data, dict) and data.get("service") == service:
                logger.info(f"Loaded seed logs for {service} from {f.name}")
                return data.get("logs", [])
            if isinstance(data, list):
                logger.info(f"Loaded seed logs from {f.name}")
                return data

    # Fall back to generic mock
    mock_file = MOCK_DIR / "datadog_logs.json"
    if mock_file.exists():
        with open(mock_file) as f:
            data = json.load(f)
            logger.info(f"Loaded mock logs from {mock_file.name}")
            return data.get("logs", data) if isinstance(data, dict) else data

    logger.warning("No mock logs found — returning empty log set")
    return []


def _fetch_real_logs(
    service: str,
    alert_time: str,
    window_minutes: int,
) -> list[dict]:
    """Query Datadog Logs API for real log data."""
    if not settings.DATADOG_API_KEY or not settings.DATADOG_APP_KEY:
        raise RuntimeError("Datadog API keys not configured")

    try:
        alert_dt = datetime.fromisoformat(alert_time.replace("Z", "+00:00"))
    except ValueError:
        alert_dt = datetime.utcnow()

    start = alert_dt - timedelta(minutes=window_minutes)
    end = alert_dt + timedelta(minutes=window_minutes)

    headers = {
        "DD-API-KEY": settings.DATADOG_API_KEY,
        "DD-APPLICATION-KEY": settings.DATADOG_APP_KEY,
        "Content-Type": "application/json",
    }

    body = {
        "filter": {
            "query": f"service:{service}",
            "from": start.isoformat() + "Z",
            "to": end.isoformat() + "Z",
        },
        "sort": "timestamp",
        "page": {"limit": 5000},
    }

    logs = []
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(DATADOG_LOGS_URL, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()
            logs = data.get("data", [])
            logger.info(f"Fetched {len(logs)} logs from Datadog for {service}")
    except httpx.HTTPError as e:
        logger.error(f"Datadog API error: {e}")
        raise

    return logs
