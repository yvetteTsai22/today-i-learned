import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.routers.notes import get_cognee_service, get_digest_cache_service, get_search_cache_service


@pytest.fixture
def mock_cognee_service():
    """Create a mock CogneeService."""
    mock = MagicMock()
    mock.add_note = AsyncMock(return_value="note-123")
    mock.search = AsyncMock(return_value=[
        {"id": "r1", "content": "result text", "source": "manual", "tags": [], "created_at": "2026-02-18T12:00:00"}
    ])
    mock.update_note = AsyncMock(return_value=True)
    mock.delete_note = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_cache_service():
    """Create a mock DigestCacheService."""
    mock = MagicMock()
    mock.invalidate_current_week = AsyncMock()
    return mock


@pytest.fixture
def mock_search_cache_service():
    """Create a mock SearchCacheService (cache miss by default)."""
    mock = MagicMock()
    mock.get_cached_search = AsyncMock(return_value=None)
    mock.store_search = AsyncMock()
    return mock


@pytest.fixture
def client(mock_cognee_service, mock_cache_service, mock_search_cache_service):
    """Create test client with mocked CogneeService."""
    app.dependency_overrides[get_cognee_service] = lambda: mock_cognee_service
    app.dependency_overrides[get_digest_cache_service] = lambda: mock_cache_service
    app.dependency_overrides[get_search_cache_service] = lambda: mock_search_cache_service
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


def test_create_note_invalidates_digest_cache(client, mock_cache_service):
    response = client.post(
        "/notes",
        json={"content": "New learning about caching"}
    )
    assert response.status_code == 201
    mock_cache_service.invalidate_current_week.assert_called_once()


def test_update_note_returns_200(client):
    response = client.put(
        "/notes/note-123",
        json={"content": "Updated content", "tags": ["updated"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated content"
    assert "updated" in data["tags"]


def test_update_note_empty_content_returns_422(client):
    response = client.put(
        "/notes/note-123",
        json={"content": ""}
    )
    assert response.status_code == 422


def test_update_note_invalidates_digest_cache(client, mock_cache_service):
    client.put(
        "/notes/note-123",
        json={"content": "Updated content"}
    )
    mock_cache_service.invalidate_current_week.assert_called()


def test_delete_note_returns_204(client):
    response = client.delete("/notes/note-123")
    assert response.status_code == 204


def test_delete_note_invalidates_digest_cache(client, mock_cache_service):
    client.delete("/notes/note-123")
    mock_cache_service.invalidate_current_week.assert_called()


def test_search_hit_returns_cached_results_without_calling_cognee(
    client, mock_cognee_service, mock_search_cache_service
):
    cached_results = [
        {"id": "c1", "content": "cached result", "source": "manual", "tags": ["cache"], "created_at": "2026-03-01T10:00:00"}
    ]
    mock_search_cache_service.get_cached_search = AsyncMock(return_value=cached_results)

    response = client.post("/search", json={"query": "test query"})

    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["content"] == "cached result"
    assert data["results"][0]["id"] == "c1"
    mock_cognee_service.search.assert_not_called()


def test_search_miss_calls_cognee_and_stores_cache(
    client, mock_cognee_service, mock_search_cache_service
):
    mock_search_cache_service.get_cached_search = AsyncMock(return_value=None)

    response = client.post("/search", json={"query": "test query"})

    assert response.status_code == 200
    mock_cognee_service.search.assert_called_once()
    mock_search_cache_service.store_search.assert_called_once()
