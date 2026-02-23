import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.routers.stats import get_stats_service


@pytest.fixture
def mock_stats_service():
    mock = MagicMock()
    mock.get_graph = AsyncMock(return_value={
        "nodes": [
            {"id": "n1", "label": "DocumentChunk", "content": "Test note about Python"},
            {"id": "n2", "label": "Entity", "content": "Python"},
            {"id": "n3", "label": "Entity", "content": "Programming"},
        ],
        "edges": [
            {"source": "n1", "target": "n2", "type": "mentions"},
            {"source": "n2", "target": "n3", "type": "related_to"},
        ],
    })
    return mock


@pytest.fixture
def client(mock_stats_service):
    app.dependency_overrides[get_stats_service] = lambda: mock_stats_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_graph_returns_nodes_and_edges(client):
    response = client.get("/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 3
    assert len(data["edges"]) == 2


def test_get_graph_node_shape(client):
    response = client.get("/graph")
    data = response.json()
    node = data["nodes"][0]
    assert "id" in node
    assert "label" in node
    assert "content" in node


def test_get_graph_edge_shape(client):
    response = client.get("/graph")
    data = response.json()
    edge = data["edges"][0]
    assert "source" in edge
    assert "target" in edge
    assert "type" in edge
