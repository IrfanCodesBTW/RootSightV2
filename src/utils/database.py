import logging

from sqlmodel import SQLModel, create_engine, Session
from .config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL, echo=False)


def create_db_and_tables():
    """Create all database tables. Safe to call multiple times (idempotent)."""
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("database.create_db_and_tables.success")
    except Exception as e:
        logger.error("database.create_db_and_tables.failed error=%s", e)
        raise


def get_session():
    """Yield a database session using a context manager to prevent connection leaks."""
    with Session(engine) as session:
        yield session
