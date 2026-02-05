"""Tests for ZettlClient."""

import pytest
from unittest.mock import patch, MagicMock

from zettl_mcp.client import ZettlClient


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
