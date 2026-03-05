import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.routers.stats import get_stats_service


@pytest.fixture
def mock_stats_service():
    mock = MagicMock()
    mock.get_activity = AsyncMock(return_value=[
        {"type": "note", "label": "Note captured", "timestamp": "2026-03-03T10:00:00", "preview": "some note text"},
        {"type": "search", "label": 'Searched: "cognee"', "timestamp": "2026-03-03T09:00:00", "preview": "result snippet"},
        {"type": "digest", "label": "Digest generated", "timestamp": "2026-03-02T14:00:00", "preview": None},
    ])
    return mock


@pytest.fixture
def client(mock_stats_service):
    app.dependency_overrides[get_stats_service] = lambda: mock_stats_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_activity_returns_200(client):
    """AC #1: GET /activity returns 200 with items list."""
    response = client.get("/activity")
    assert response.status_code == 200


def test_get_activity_response_shape(client):
    """AC #1, #2: Response contains 'items' key with a list."""
    response = client.get("/activity")
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 3


def test_get_activity_item_fields(client):
    """AC #2: Each item has type, label, timestamp, preview fields."""
    response = client.get("/activity")
    data = response.json()
    for item in data["items"]:
        assert "type" in item
        assert "label" in item
        assert "timestamp" in item
        assert "preview" in item
    # Validate type values are one of the allowed literals
    types = {item["type"] for item in data["items"]}
    assert types <= {"note", "search", "digest"}


def test_get_activity_default_limit(client, mock_stats_service):
    """AC #3: Default limit of 20 is passed to the service."""
    client.get("/activity")
    mock_stats_service.get_activity.assert_called_once_with(limit=20)


def test_get_activity_custom_limit(client, mock_stats_service):
    """AC #4: Custom limit=5 is passed to the service."""
    client.get("/activity?limit=5")
    mock_stats_service.get_activity.assert_called_once_with(limit=5)


def test_get_activity_empty_returns_empty_list(client, mock_stats_service):
    """AC #5: When no activity exists, returns empty items list."""
    mock_stats_service.get_activity = AsyncMock(return_value=[])
    response = client.get("/activity")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
