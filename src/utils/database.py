from sqlmodel import SQLModel, create_engine, Session
from .config import settings

# In a real app, this would be in config
sqlite_url = "sqlite:///./rootsight.db"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
