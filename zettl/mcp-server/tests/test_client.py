"""Tests for ZettlClient."""

import pytest
from unittest.mock import patch, MagicMock

import httpx

from zettl_mcp.client import ZettlClient, ZettlAPIError


@pytest.mark.anyio
async def test_health_check_success():
    """Client returns health status when API is healthy."""
    client = ZettlClient(base_url="http://test:8000")

    with patch.object(client._http, "get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = await client.health_check()

        assert result == {"status": "healthy"}


@pytest.mark.anyio
async def test_health_check_network_error():
    """Client returns friendly message when API unreachable."""
    client = ZettlClient(base_url="http://test:8000")

    with patch.object(client._http, "get") as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(ZettlAPIError) as exc_info:
            await client.health_check()

        assert "Cannot reach Zettl API" in str(exc_info.value)


@pytest.mark.anyio
async def test_health_check_server_error():
    """Client wraps 5xx errors with context."""
    client = ZettlClient(base_url="http://test:8000")

    with patch.object(client._http, "get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=MagicMock(),
            response=mock_response,
        )
        mock_get.return_value = mock_response

        with pytest.raises(ZettlAPIError) as exc_info:
            await client.health_check()

        assert "Zettl API error" in str(exc_info.value)


@pytest.mark.anyio
async def test_add_note_success():
    """Client sends note to API and returns response."""
    client = ZettlClient(base_url="http://test:8000")

    with patch.object(client._http, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "note-123",
            "content": "Test note",
            "source": "agent",
            "tags": ["test"],
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = await client.add_note(
            content="Test note",
            tags=["test"],
            source="agent",
        )

        assert result["id"] == "note-123"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[0][0] == "/notes"
        assert call_kwargs[1]["json"]["content"] == "Test note"


@pytest.mark.anyio
async def test_search_success():
    """Client searches knowledge graph and returns results."""
    client = ZettlClient(base_url="http://test:8000")

    with patch.object(client._http, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": ["Result 1", "Result 2"],
            "query": "test query",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = await client.search(
            query="test query",
            search_type="graph_completion",
        )

        assert result["results"] == ["Result 1", "Result 2"]
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[0][0] == "/search"
        assert call_kwargs[1]["json"]["query"] == "test query"
        assert call_kwargs[1]["json"]["search_type"] == "graph_completion"


@pytest.mark.anyio
async def test_generate_digest_success():
    """Client generates weekly digest."""
    client = ZettlClient(base_url="http://test:8000")

    with patch.object(client._http, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "digest-123",
            "summary": "Weekly summary",
            "suggested_topics": [
                {"title": "Topic 1", "reasoning": "Because..."}
            ],
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = await client.generate_digest()

        assert result["summary"] == "Weekly summary"
        assert len(result["suggested_topics"]) == 1
        mock_post.assert_called_once_with("/digest", timeout=120.0, params={})


@pytest.mark.anyio
async def test_generate_digest_force_refresh():
    """Client passes force_refresh query param when requested."""
    client = ZettlClient(base_url="http://test:8000")

    with patch.object(client._http, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "digest-456",
            "summary": "Fresh summary",
            "suggested_topics": [],
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = await client.generate_digest(force_refresh=True)

        assert result["summary"] == "Fresh summary"
        mock_post.assert_called_once_with(
            "/digest", timeout=120.0, params={"force_refresh": "true"}
        )


@pytest.mark.anyio
async def test_generate_content_success():
    """Client generates content in requested formats."""
    client = ZettlClient(base_url="http://test:8000")

    with patch.object(client._http, "post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "topic": "AI Testing",
            "blog": "# Blog Post\n\nContent here...",
            "linkedin": "Excited to share...",
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = await client.generate_content(
            topic="AI Testing",
            source_chunks=["chunk 1", "chunk 2"],
            formats=["blog", "linkedin"],
        )

        assert result["topic"] == "AI Testing"
        assert "blog" in result
        assert "linkedin" in result
        call_kwargs = mock_post.call_args
        assert call_kwargs[0][0] == "/digest/content"


@pytest.mark.anyio
async def test_timeout_uses_default_for_health_check():
    """Health check uses the default 30s timeout."""
    client = ZettlClient(base_url="http://test:8000")

    with patch.object(client._http, "get") as mock_get:
        mock_get.side_effect = httpx.TimeoutException("timed out")

        with pytest.raises(ZettlAPIError) as exc_info:
            await client.health_check()

        assert "timeout after 30s" in str(exc_info.value)


@pytest.mark.anyio
async def test_timeout_uses_long_timeout_for_add_note():
    """add_note uses the longer 120s timeout for cognify processing."""
    client = ZettlClient(base_url="http://test:8000")

    with patch.object(client._http, "post") as mock_post:
        mock_post.side_effect = httpx.TimeoutException("timed out")

        with pytest.raises(ZettlAPIError) as exc_info:
            await client.add_note(content="Test note")

        assert "timeout after 120s" in str(exc_info.value)
