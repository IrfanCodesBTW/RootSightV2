"""
RootSight — Incident Store

JSON file-based persistence for completed incident briefs.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

from src.config import INCIDENTS_DIR
from src.schemas.incident import IncidentBrief
from src.utils.logger import get_logger

logger = get_logger("services.incident_store")


def save(brief: IncidentBrief) -> Path:
    """
    Save an incident brief to disk as JSON.

    Returns the path to the saved file.
    """
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = INCIDENTS_DIR / f"{brief.incident_id}.json"
    with open(path, "w") as f:
        json.dump(brief.model_dump(), f, indent=2, default=str)
    logger.info(f"Saved incident brief: {path}")
    return path


def load(incident_id: str) -> Optional[IncidentBrief]:
    """Load an incident brief from disk by ID."""
    path = INCIDENTS_DIR / f"{incident_id}.json"
    if not path.exists():
        logger.warning(f"Incident not found: {incident_id}")
        return None
    with open(path) as f:
        data = json.load(f)
    return IncidentBrief(**data)


def list_all() -> list[str]:
    """List all stored incident IDs."""
    if not INCIDENTS_DIR.exists():
        return []
    return [f.stem for f in INCIDENTS_DIR.glob("*.json")]
