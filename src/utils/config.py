from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

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

settings = Settings()
