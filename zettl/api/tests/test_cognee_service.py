import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_add_note_calls_cognee_add():
    with patch("app.services.cognee_service.cognee") as mock_cognee:
        mock_cognee.add = AsyncMock()
        mock_cognee.cognify = AsyncMock()

        from app.services.cognee_service import CogneeService
        service = CogneeService()

        await service.add_note("Test content", dataset_name="test")

        mock_cognee.add.assert_called_once()
        mock_cognee.cognify.assert_called_once()


@pytest.mark.asyncio
async def test_search_returns_results():
    with patch("app.services.cognee_service.cognee") as mock_cognee:
        mock_cognee.search = AsyncMock(return_value=["result1", "result2"])

        from app.services.cognee_service import CogneeService
        service = CogneeService()

        results = await service.search("query")

        assert len(results) == 2
