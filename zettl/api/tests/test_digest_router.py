import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.routers.digest import get_cognee_service, get_llm_service


@pytest.fixture
def mock_cognee_service():
    """Create a mock CogneeService."""
    mock = MagicMock()
    mock.search = AsyncMock(return_value=["chunk1", "chunk2"])
    return mock


@pytest.fixture
def mock_llm_service():
    """Create a mock LLMService."""
    mock = MagicMock()
    mock.generate_digest_summary = AsyncMock(return_value={
        "summary": "This week you learned about graphs",
        "topics": [
            {"title": "Graph DBs", "reasoning": "Interesting pattern", "relevant_chunks": ["chunk1"]}
        ]
    })
    mock.generate_blog_draft = AsyncMock(return_value="# Blog content")
    mock.generate_linkedin_post = AsyncMock(return_value="LinkedIn post")
    mock.generate_x_thread = AsyncMock(return_value="1/ Thread")
    mock.generate_video_script = AsyncMock(return_value="[HOOK] Script")
    return mock


@pytest.fixture
def client(mock_cognee_service, mock_llm_service):
    """Create test client with mocked services."""
    app.dependency_overrides[get_cognee_service] = lambda: mock_cognee_service
    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_digest_returns_201(client):
    response = client.post("/digest")
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "summary" in data
    assert "suggested_topics" in data


def test_generate_content_for_topic(client):
    response = client.post(
        "/digest/content",
        json={
            "topic": "Graph Databases",
            "source_chunks": ["chunk1", "chunk2"],
            "formats": ["blog", "linkedin"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "blog" in data
    assert "linkedin" in data
