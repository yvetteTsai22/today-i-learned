from unittest.mock import AsyncMock, MagicMock, patch

from app.services.stats_service import StatsService


class _AsyncIterator:
    """Async iterator wrapper for mocking Neo4j result iteration."""

    def __init__(self, items):
        self._items = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._items)
        except StopIteration:
            raise StopAsyncIteration


def _make_mock_driver_with_records(records):
    """Create a mock Neo4j driver that supports async iteration over records.

    Unlike the single-record mock (result.single()), this mock supports
    `async for record in result` for queries returning multiple rows.
    """
    mock_result = _AsyncIterator(records)

    mock_session = AsyncMock()
    mock_session.run = AsyncMock(return_value=mock_result)

    mock_context = MagicMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context.__aexit__ = AsyncMock(return_value=None)

    mock_driver = MagicMock()
    mock_driver.session = MagicMock(return_value=mock_context)

    return mock_driver, mock_session


@patch("app.services.stats_service.AsyncGraphDatabase")
async def test_get_activity_returns_list(mock_agd):
    """AC #1: get_activity returns a list of dicts."""
    records = [
        {"type": "note", "ts": "2026-03-05T10:00:00", "label_text": "Note captured", "preview_text": "Hello world"},
        {"type": "search", "ts": "2026-03-05T09:00:00", "label_text": 'Searched: "test"', "preview_text": "result"},
    ]
    driver, session = _make_mock_driver_with_records(records)
    mock_agd.driver.return_value = driver

    service = StatsService()
    result = await service.get_activity()

    assert isinstance(result, list)
    assert len(result) == 2


@patch("app.services.stats_service.AsyncGraphDatabase")
async def test_get_activity_item_shape(mock_agd):
    """AC #1, #3: Each item has type, label, timestamp, preview keys with correct mapping."""
    records = [
        {"type": "note", "ts": "2026-03-05T10:00:00", "label_text": "Note captured", "preview_text": "Some note text"},
    ]
    driver, session = _make_mock_driver_with_records(records)
    mock_agd.driver.return_value = driver

    service = StatsService()
    result = await service.get_activity()

    item = result[0]
    assert item["type"] == "note"
    assert item["label"] == "Note captured"
    assert item["timestamp"] == "2026-03-05T10:00:00"
    assert item["preview"] == "Some note text"


@patch("app.services.stats_service.AsyncGraphDatabase")
async def test_get_activity_empty_preview_becomes_none(mock_agd):
    """AC #5: Empty preview_text (e.g. digest) is converted to None."""
    records = [
        {"type": "digest", "ts": "2026-03-05T08:00:00", "label_text": "Digest generated", "preview_text": ""},
    ]
    driver, session = _make_mock_driver_with_records(records)
    mock_agd.driver.return_value = driver

    service = StatsService()
    result = await service.get_activity()

    assert result[0]["preview"] is None


@patch("app.services.stats_service.AsyncGraphDatabase")
async def test_get_activity_passes_limit_to_query(mock_agd):
    """AC #6: The limit parameter is passed to the Cypher query."""
    driver, session = _make_mock_driver_with_records([])
    mock_agd.driver.return_value = driver

    service = StatsService()
    await service.get_activity(limit=5)

    session.run.assert_called_once()
    call_kwargs = session.run.call_args
    # The limit should be passed as a keyword argument to session.run
    assert call_kwargs[1]["limit"] == 5
