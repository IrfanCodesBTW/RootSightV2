"""
RootSight — Central Configuration

Loads environment variables and provides typed configuration
for all modules across the project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SEED_DIR = DATA_DIR / "seed"
MOCK_DIR = DATA_DIR / "mock"
INCIDENTS_DIR = DATA_DIR / "incidents"
MEMORY_DIR = DATA_DIR / "memory"

# Ensure data directories exist
for d in [INCIDENTS_DIR, MEMORY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    load_dotenv(_env_file)


class Settings:
    """Typed access to all configuration values."""

    # --- LLM ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # --- Demo mode ---
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "true").lower() == "true"

    # --- Datadog ---
    DATADOG_API_KEY: str = os.getenv("DATADOG_API_KEY", "")
    DATADOG_APP_KEY: str = os.getenv("DATADOG_APP_KEY", "")
    DATADOG_SITE: str = os.getenv("DATADOG_SITE", "datadoghq.com")

    # --- PagerDuty ---
    PAGERDUTY_API_KEY: str = os.getenv("PAGERDUTY_API_KEY", "")

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # --- Vector Store ---
    SIMILARITY_THRESHOLD: float = 0.5
    FAISS_INDEX_PATH: Path = MEMORY_DIR / "incident_index.faiss"
    FAISS_METADATA_PATH: Path = MEMORY_DIR / "incident_metadata.pkl"

    # --- Performance ---
    LLM_RETRY_ATTEMPTS: int = 3
    LLM_RETRY_BASE_DELAY: float = 2.0  # seconds, exponential backoff
    LOG_TIME_WINDOW_MINUTES: int = 30  # ± from alert time

    @property
    def has_gemini_key(self) -> bool:
        return bool(self.GEMINI_API_KEY) and self.GEMINI_API_KEY != "your-gemini-api-key-here"


settings = Settings()
