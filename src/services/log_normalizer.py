"""
RootSight — Log Normalizer

Transforms raw logs into the NormalizedLogSet schema.
Handles normalization, noise filtering, and deduplication.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional

from src.schemas.logs import NormalizedLogEntry, NormalizedLogSet, DataQuality
from src.utils.logger import get_logger

logger = get_logger("services.normalizer")

# Patterns considered noise (health checks, heartbeats, etc.)
NOISE_PATTERNS = [
    "health check",
    "healthcheck",
    "/health",
    "/ready",
    "/live",
    "heartbeat",
    "keep-alive",
    "OPTIONS /",
    "kube-probe",
    "ELB-HealthChecker",
]

# Log levels to filter out in noise reduction
NOISE_LEVELS = {"DEBUG", "TRACE"}


def normalize_logs(
    incident_id: str,
    raw_logs: list[dict],
    alert_time: Optional[str] = None,
    window_minutes: int = 30,
) -> NormalizedLogSet:
    """
    Normalize raw log entries into a structured NormalizedLogSet.

    Steps:
        1. Parse each entry into NormalizedLogEntry
        2. Filter noise (health checks, debug spam)
        3. Deduplicate near-identical entries within 5-second windows
        4. Assess data quality

    Args:
        incident_id: Incident identifier.
        raw_logs: Raw log entries from Datadog or mock.
        alert_time: ISO-8601 alert timestamp for time window calculation.
        window_minutes: Time window radius.

    Returns:
        NormalizedLogSet with filtered, deduplicated logs.
    """
    total_raw = len(raw_logs)
    logger.info(f"Normalizing {total_raw} raw log entries")

    # Step 1: Parse into NormalizedLogEntry
    parsed = []
    for entry in raw_logs:
        try:
            normalized = _parse_entry(entry)
            if normalized:
                parsed.append(normalized)
        except Exception as e:
            logger.debug(f"Failed to parse log entry: {e}")

    # Step 2: Filter noise
    filtered = [e for e in parsed if not _is_noise(e)]
    noise_removed = len(parsed) - len(filtered)
    logger.info(f"Noise filtering: {noise_removed} noisy entries removed, {len(filtered)} remaining")

    # Step 3: Deduplicate
    deduped = _deduplicate(filtered, window_seconds=5)
    dupes_removed = len(filtered) - len(deduped)
    logger.info(f"Deduplication: {dupes_removed} duplicates removed, {len(deduped)} remaining")

    # Step 4: Sort chronologically
    deduped.sort(key=lambda e: e.timestamp)

    # Step 5: Assess quality
    quality = _assess_quality(deduped, total_raw)

    # Compute time window
    time_window = {}
    if alert_time:
        try:
            alert_dt = datetime.fromisoformat(alert_time.replace("Z", "+00:00"))
            time_window = {
                "start": (alert_dt - timedelta(minutes=window_minutes)).isoformat() + "Z",
                "end": (alert_dt + timedelta(minutes=window_minutes)).isoformat() + "Z",
            }
        except ValueError:
            pass

    deploy_markers = any(
        "deploy" in e.message.lower() or "release" in e.message.lower()
        for e in deduped
    )
    quality.deploy_markers_found = deploy_markers

    return NormalizedLogSet(
        incident_id=incident_id,
        source="datadog",
        time_window=time_window,
        total_raw_count=total_raw,
        filtered_count=len(deduped),
        data_quality=quality,
        logs=deduped,
    )


def _parse_entry(raw: dict) -> Optional[NormalizedLogEntry]:
    """Parse a single raw log entry into a NormalizedLogEntry."""
    # Handle multiple common log formats
    timestamp = (
        raw.get("timestamp")
        or raw.get("@timestamp")
        or raw.get("date")
        or raw.get("time")
        or ""
    )
    level = (
        raw.get("level")
        or raw.get("severity")
        or raw.get("status")
        or "INFO"
    ).upper()
    service = (
        raw.get("service")
        or raw.get("source")
        or raw.get("app")
        or "unknown"
    )
    message = (
        raw.get("message")
        or raw.get("msg")
        or raw.get("content")
        or raw.get("text")
        or ""
    )
    metadata = {}
    for key in ("trace_id", "span_id", "host", "pod", "container", "request_id"):
        if key in raw:
            metadata[key] = raw[key]

    if not timestamp or not message:
        return None

    return NormalizedLogEntry(
        timestamp=timestamp,
        level=level,
        service=service,
        message=message,
        metadata=metadata,
    )


def _is_noise(entry: NormalizedLogEntry) -> bool:
    """Check if a log entry is noise (health checks, debug spam, etc.)."""
    if entry.level in NOISE_LEVELS:
        return True
    msg_lower = entry.message.lower()
    return any(pattern in msg_lower for pattern in NOISE_PATTERNS)


def _deduplicate(entries: list[NormalizedLogEntry], window_seconds: int = 5) -> list[NormalizedLogEntry]:
    """Remove near-identical entries within a time window."""
    if not entries:
        return entries

    result = [entries[0]]
    for entry in entries[1:]:
        prev = result[-1]
        # Check if same service + same message within window
        if entry.service == prev.service and entry.message == prev.message:
            try:
                t1 = datetime.fromisoformat(prev.timestamp.replace("Z", "+00:00"))
                t2 = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
                if abs((t2 - t1).total_seconds()) <= window_seconds:
                    continue  # Skip duplicate
            except ValueError:
                pass
        result.append(entry)

    return result


def _assess_quality(entries: list[NormalizedLogEntry], raw_count: int) -> DataQuality:
    """Assess the quality of the normalized log set."""
    if raw_count == 0:
        return DataQuality(completeness="low", noise_level="unknown", confidence_impact="significant")

    ratio = len(entries) / raw_count if raw_count > 0 else 0

    # Completeness: based on how many entries survived filtering
    if len(entries) > 50:
        completeness = "high"
    elif len(entries) > 10:
        completeness = "medium"
    else:
        completeness = "low"

    # Noise level: based on how much we filtered out
    if ratio > 0.5:
        noise_level = "low"
    elif ratio > 0.1:
        noise_level = "medium"
    else:
        noise_level = "high"

    # Confidence impact
    if completeness == "high" and noise_level != "high":
        confidence_impact = "none"
    elif completeness == "low":
        confidence_impact = "significant"
    else:
        confidence_impact = "minor"

    return DataQuality(
        completeness=completeness,
        noise_level=noise_level,
        confidence_impact=confidence_impact,
    )
