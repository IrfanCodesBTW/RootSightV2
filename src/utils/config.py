import logging
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # AI APIs
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Integrations
    DATADOG_API_KEY: Optional[str] = None
    DATADOG_APP_KEY: Optional[str] = None
    PAGERDUTY_INTEGRATION_KEY: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None
    JIRA_BASE_URL: Optional[str] = None
    JIRA_PROJECT_KEY: Optional[str] = None
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_CHANNEL_ID: Optional[str] = None

    # App config
    DATABASE_URL: str = "sqlite:///./rootsight.db"
    FAISS_INDEX_PATH: str = "./storage/incident_index.faiss"
    LOG_LEVEL: str = "INFO"
    DEMO_MODE: bool = True
    MAX_LOG_LINES: int = 100
    TIMELINE_MAX_TOKENS: int = 3000
    CORS_ORIGINS: str = "http://localhost:3000"
    GEMINI_MODEL: str = "models/gemini-flash-latest"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"
    API_ERROR_DETAIL_IN_RESPONSE: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_api_keys(self):
        """Raise ValueError if API keys are missing when not in demo mode."""
        if not self.DEMO_MODE:
            missing = []
            if not self.GEMINI_API_KEY or not self.GEMINI_API_KEY.strip():
                missing.append("GEMINI_API_KEY")
            if not self.GROQ_API_KEY or not self.GROQ_API_KEY.strip():
                missing.append("GROQ_API_KEY")
            if missing:
                raise ValueError(
                    f"Missing required API keys: {', '.join(missing)}. "
                    f"Set them in .env or enable DEMO_MODE=true for offline operation."
                )
        return self


settings = Settings()
