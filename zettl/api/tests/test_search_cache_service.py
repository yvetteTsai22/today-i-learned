import json

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.search_cache_service import SearchCacheService


def _make_mock_driver():
    """Create a mock Neo4j async driver + session.

    Neo4j's AsyncDriver.session() is a regular (non-async) method that
    returns an async context manager, so driver must be MagicMock (not
    AsyncMock) to avoid wrapping .session() in a coroutine.
    """
    driver = MagicMock()
    session = AsyncMock()
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=session)
    ctx.__aexit__ = AsyncMock(return_value=False)
    driver.session.return_value = ctx
    return driver, session


@pytest.mark.asyncio
@patch("app.services.search_cache_service.AsyncGraphDatabase")
async def test_get_cached_search_returns_none_on_miss(mock_agd):
    driver, session = _make_mock_driver()
    mock_agd.driver.return_value = driver

    result_mock = AsyncMock()
    result_mock.single.return_value = None
    session.run.return_value = result_mock

    service = SearchCacheService()
    result = await service.get_cached_search("some query")

    assert result is None
    session.run.assert_called_once()
    query_arg = session.run.call_args[0][0]
    assert "MATCH" in query_arg
    assert "CachedSearch" in query_arg


@pytest.mark.asyncio
@patch("app.services.search_cache_service.AsyncGraphDatabase")
async def test_get_cached_search_returns_results_on_hit(mock_agd):
    driver, session = _make_mock_driver()
    mock_agd.driver.return_value = driver

    stored_results = [{"content": "result one"}, {"content": "result two"}]
    node = {
        "results_json": json.dumps(stored_results),
    }
    record = {"s": node}
    result_mock = AsyncMock()
    result_mock.single.return_value = record
    session.run.return_value = result_mock

    service = SearchCacheService()
    result = await service.get_cached_search("test query")

    assert result is not None
    assert result == stored_results


@pytest.mark.asyncio
@patch("app.services.search_cache_service.AsyncGraphDatabase")
async def test_get_cached_search_normalizes_query(mock_agd):
    driver, session = _make_mock_driver()
    mock_agd.driver.return_value = driver

    result_mock = AsyncMock()
    result_mock.single.return_value = None
    session.run.return_value = result_mock

    service = SearchCacheService()
    await service.get_cached_search("  My Query  ")

    params = session.run.call_args[1]
    assert params["query"] == "my query"


@pytest.mark.asyncio
@patch("app.services.search_cache_service.AsyncGraphDatabase")
async def test_store_search_writes_node_with_expiry(mock_agd):
    driver, session = _make_mock_driver()
    mock_agd.driver.return_value = driver
    session.run.return_value = AsyncMock()

    results = [{"content": "some content"}]
    service = SearchCacheService()
    await service.store_search("my query", results)

    session.run.assert_called_once()
    query_arg = session.run.call_args[0][0]
    assert "MERGE" in query_arg
    assert "CachedSearch" in query_arg

    params = session.run.call_args[1]
    assert params["query"] == "my query"
    assert params["results_json"] == json.dumps(results)
    assert "created_at" in params
    assert "expires_at" in params

    # Verify expiry is ~24h after creation
    created = datetime.fromisoformat(params["created_at"])
    expires = datetime.fromisoformat(params["expires_at"])
    diff = expires - created
    assert timedelta(hours=23, minutes=59) <= diff <= timedelta(hours=24, minutes=1)


@pytest.mark.asyncio
@patch("app.services.search_cache_service.AsyncGraphDatabase")
async def test_store_search_truncates_preview_to_80_chars(mock_agd):
    driver, session = _make_mock_driver()
    mock_agd.driver.return_value = driver
    session.run.return_value = AsyncMock()

    long_content = "A" * 200
    results = [{"content": long_content}]
    service = SearchCacheService()
    await service.store_search("query", results)

    params = session.run.call_args[1]
    assert len(params["preview"]) == 80
    assert params["preview"] == "A" * 80


@pytest.mark.asyncio
@patch("app.services.search_cache_service.AsyncGraphDatabase")
async def test_store_search_empty_results_uses_empty_preview(mock_agd):
    driver, session = _make_mock_driver()
    mock_agd.driver.return_value = driver
    session.run.return_value = AsyncMock()

    service = SearchCacheService()
    await service.store_search("query", [])

    params = session.run.call_args[1]
    assert params["preview"] == ""
