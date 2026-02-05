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
