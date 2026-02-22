import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.digest import DigestResponse, TopicSuggestion
from app.services.digest_cache_service import DigestCacheService


@pytest.fixture
def sample_digest():
    """A sample DigestResponse for testing."""
    return DigestResponse(
        id="digest-123",
        summary="This week you learned about caching",
        suggested_topics=[
            TopicSuggestion(
                title="Caching Strategies",
                reasoning="Important pattern",
                relevant_chunks=["chunk1", "chunk2"],
            )
        ],
        week_start=datetime(2026, 2, 16, 0, 0, 0),
        week_end=datetime(2026, 2, 22, 23, 59, 59),
        created_at=datetime(2026, 2, 18, 12, 0, 0),
    )


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
@patch("app.services.digest_cache_service.AsyncGraphDatabase")
async def test_get_cached_digest_returns_none_on_miss(mock_agd):
    driver, session = _make_mock_driver()
    mock_agd.driver.return_value = driver

    result_mock = AsyncMock()
    result_mock.single.return_value = None
    session.run.return_value = result_mock

    service = DigestCacheService()
    result = await service.get_cached_digest(2026, 8)

    assert result is None
    session.run.assert_called_once()
    query_arg = session.run.call_args[0][0]
    assert "MATCH" in query_arg
    assert "CachedDigest" in query_arg


@pytest.mark.asyncio
@patch("app.services.digest_cache_service.AsyncGraphDatabase")
async def test_get_cached_digest_returns_digest_on_hit(mock_agd, sample_digest):
    driver, session = _make_mock_driver()
    mock_agd.driver.return_value = driver

    topics_json = json.dumps(
        [t.model_dump(mode="json") for t in sample_digest.suggested_topics]
    )
    node = {
        "digest_id": sample_digest.id,
        "summary": sample_digest.summary,
        "topics_json": topics_json,
        "week_start": sample_digest.week_start.isoformat(),
        "week_end": sample_digest.week_end.isoformat(),
        "created_at": sample_digest.created_at.isoformat(),
    }
    record = {"d": node}
    result_mock = AsyncMock()
    result_mock.single.return_value = record
    session.run.return_value = result_mock

    service = DigestCacheService()
    result = await service.get_cached_digest(2026, 8)

    assert result is not None
    assert isinstance(result, DigestResponse)
    assert result.id == "digest-123"
    assert result.summary == "This week you learned about caching"
    assert len(result.suggested_topics) == 1
    assert result.suggested_topics[0].title == "Caching Strategies"


@pytest.mark.asyncio
@patch("app.services.digest_cache_service.AsyncGraphDatabase")
async def test_store_digest_runs_merge_query(mock_agd, sample_digest):
    driver, session = _make_mock_driver()
    mock_agd.driver.return_value = driver
    session.run.return_value = AsyncMock()

    service = DigestCacheService()
    await service.store_digest(2026, 8, sample_digest)

    session.run.assert_called_once()
    query_arg = session.run.call_args[0][0]
    assert "MERGE" in query_arg
    assert "CachedDigest" in query_arg

    params = session.run.call_args[1]
    assert params["year"] == 2026
    assert params["week"] == 8
    assert params["digest_id"] == sample_digest.id


@pytest.mark.asyncio
@patch("app.services.digest_cache_service.AsyncGraphDatabase")
async def test_invalidate_current_week_deletes_node(mock_agd):
    driver, session = _make_mock_driver()
    mock_agd.driver.return_value = driver
    session.run.return_value = AsyncMock()

    service = DigestCacheService()
    await service.invalidate_current_week()

    session.run.assert_called_once()
    query_arg = session.run.call_args[0][0]
    assert "DELETE" in query_arg
    assert "CachedDigest" in query_arg

    params = session.run.call_args[1]
    now = datetime.now()
    iso_year, iso_week, _ = now.isocalendar()
    assert params["year"] == iso_year
    assert params["week"] == iso_week
