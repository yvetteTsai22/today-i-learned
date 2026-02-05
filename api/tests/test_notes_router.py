import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.routers.notes import get_cognee_service


@pytest.fixture
def mock_cognee_service():
    """Create a mock CogneeService."""
    mock = MagicMock()
    mock.add_note = AsyncMock(return_value="note-123")
    mock.search = AsyncMock(return_value=["result1"])
    return mock


@pytest.fixture
def client(mock_cognee_service):
    """Create test client with mocked CogneeService."""
    app.dependency_overrides[get_cognee_service] = lambda: mock_cognee_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_create_note_returns_201(client):
    response = client.post(
        "/notes",
        json={"content": "Test note content"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["content"] == "Test note content"


def test_create_note_with_tags(client):
    response = client.post(
        "/notes",
        json={
            "content": "Tagged note",
            "tags": ["test", "example"],
            "source": "agent"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert "test" in data["tags"]


def test_search_notes(client):
    response = client.post(
        "/search",
        json={"query": "test query"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
