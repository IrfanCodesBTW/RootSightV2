import pytest
from sqlmodel import SQLModel, Session, create_engine

# Test database
sqlite_url = "sqlite:///./test_rootsight.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})


@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def mock_gemini_response(mocker):
    async def mock_generate(*args, **kwargs):
        return {"mock": "gemini_response"}

    mocker.patch("src.features.llm_clients.gemini_client.generate", side_effect=mock_generate)
    return mock_generate


@pytest.fixture
def mock_groq_response(mocker):
    async def mock_format(*args, **kwargs):
        return {"mock": "groq_response"}

    mocker.patch("src.features.llm_clients.groq_client.format_json", side_effect=mock_format)
    return mock_format
