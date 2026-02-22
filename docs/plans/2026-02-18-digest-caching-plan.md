# Digest Caching Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Cache weekly digests in Neo4j so identical requests within the same calendar week return the stored result, invalidating when new notes are added.

**Architecture:** New `DigestCacheService` uses `neo4j` async driver (already installed via `cognee[neo4j]`) to store/retrieve `CachedDigest` nodes keyed by `(year, week)`. The digest router checks cache before generating. The notes router invalidates the cache after adding a note.

**Tech Stack:** Python 3.11+, FastAPI, neo4j async driver, pytest, pydantic

---

### Task 1: DigestCacheService — Write tests

**Files:**
- Create: `zettl/api/tests/test_digest_cache_service.py`

**Step 1: Write the failing tests**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.digest_cache_service import DigestCacheService
from app.models.digest import DigestResponse, TopicSuggestion


@pytest.fixture
def mock_driver():
    """Create a mock Neo4j async driver."""
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__aenter__ = AsyncMock(return_value=session)
    driver.session.return_value.__aexit__ = AsyncMock(return_value=None)
    session.run = AsyncMock()
    return driver, session


@pytest.fixture
def service(mock_driver):
    """Create DigestCacheService with mocked driver."""
    driver, _ = mock_driver
    with patch("app.services.digest_cache_service.AsyncGraphDatabase.driver", return_value=driver):
        svc = DigestCacheService()
    svc._driver = driver
    return svc


def _make_digest() -> DigestResponse:
    return DigestResponse(
        id="digest-123",
        summary="This week you learned about graphs",
        suggested_topics=[
            TopicSuggestion(
                title="Graph DBs",
                reasoning="Interesting pattern",
                relevant_chunks=["chunk1"],
            )
        ],
        week_start=datetime(2026, 2, 16),
        week_end=datetime(2026, 2, 22),
        created_at=datetime(2026, 2, 18, 12, 0, 0),
    )


@pytest.mark.asyncio
async def test_get_cached_digest_returns_none_on_miss(service, mock_driver):
    _, session = mock_driver
    result_mock = MagicMock()
    result_mock.single.return_value = None
    session.run = AsyncMock(return_value=result_mock)

    result = await service.get_cached_digest(2026, 8)
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_digest_returns_digest_on_hit(service, mock_driver):
    _, session = mock_driver
    digest = _make_digest()
    record = {
        "digest_id": digest.id,
        "summary": digest.summary,
        "topics_json": '[{"title": "Graph DBs", "reasoning": "Interesting pattern", "relevant_chunks": ["chunk1"]}]',
        "week_start": "2026-02-16T00:00:00",
        "week_end": "2026-02-22T00:00:00",
        "created_at": "2026-02-18T12:00:00",
    }
    single_mock = MagicMock()
    single_mock.__getitem__ = lambda self, key: record[key]
    result_mock = MagicMock()
    result_mock.single.return_value = single_mock
    session.run = AsyncMock(return_value=result_mock)

    result = await service.get_cached_digest(2026, 8)
    assert result is not None
    assert result.id == "digest-123"
    assert result.summary == "This week you learned about graphs"
    assert len(result.suggested_topics) == 1
    assert result.suggested_topics[0].title == "Graph DBs"


@pytest.mark.asyncio
async def test_store_digest_runs_merge_query(service, mock_driver):
    _, session = mock_driver
    session.run = AsyncMock()
    digest = _make_digest()

    await service.store_digest(2026, 8, digest)
    session.run.assert_called_once()
    query = session.run.call_args[0][0]
    assert "MERGE" in query
    assert "CachedDigest" in query


@pytest.mark.asyncio
async def test_invalidate_current_week_deletes_node(service, mock_driver):
    _, session = mock_driver
    session.run = AsyncMock()

    await service.invalidate_current_week()
    session.run.assert_called_once()
    query = session.run.call_args[0][0]
    assert "DELETE" in query
    assert "CachedDigest" in query
```

**Step 2: Run tests to verify they fail**

Run: `cd zettl/api && python -m pytest tests/test_digest_cache_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.digest_cache_service'`

---

### Task 2: DigestCacheService — Implement

**Files:**
- Create: `zettl/api/app/services/digest_cache_service.py`

**Step 1: Write the implementation**

```python
import json
from datetime import datetime

from neo4j import AsyncGraphDatabase

from app.config import get_settings
from app.models.digest import DigestResponse, TopicSuggestion


class DigestCacheService:
    """Cache weekly digests as Neo4j nodes."""

    def __init__(self):
        settings = get_settings()
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def get_cached_digest(self, year: int, week: int) -> DigestResponse | None:
        """Return cached digest for the given ISO year+week, or None."""
        query = """
        MATCH (d:CachedDigest {year: $year, week: $week})
        RETURN d.digest_id AS digest_id,
               d.summary AS summary,
               d.topics_json AS topics_json,
               d.week_start AS week_start,
               d.week_end AS week_end,
               d.created_at AS created_at
        """
        async with self._driver.session() as session:
            result = await session.run(query, year=year, week=week)
            record = result.single()

        if record is None:
            return None

        topics = [
            TopicSuggestion(**t)
            for t in json.loads(record["topics_json"])
        ]

        return DigestResponse(
            id=record["digest_id"],
            summary=record["summary"],
            suggested_topics=topics,
            week_start=datetime.fromisoformat(record["week_start"]),
            week_end=datetime.fromisoformat(record["week_end"]),
            created_at=datetime.fromisoformat(record["created_at"]),
        )

    async def store_digest(
        self, year: int, week: int, digest: DigestResponse
    ) -> None:
        """Store a digest, replacing any existing one for this week."""
        topics_json = json.dumps(
            [t.model_dump() for t in digest.suggested_topics]
        )
        query = """
        MERGE (d:CachedDigest {year: $year, week: $week})
        SET d.digest_id = $digest_id,
            d.summary = $summary,
            d.topics_json = $topics_json,
            d.week_start = $week_start,
            d.week_end = $week_end,
            d.created_at = $created_at
        """
        async with self._driver.session() as session:
            await session.run(
                query,
                year=year,
                week=week,
                digest_id=digest.id,
                summary=digest.summary,
                topics_json=topics_json,
                week_start=digest.week_start.isoformat(),
                week_end=digest.week_end.isoformat(),
                created_at=digest.created_at.isoformat(),
            )

    async def invalidate_current_week(self) -> None:
        """Delete the cached digest for the current ISO calendar week."""
        today = datetime.now()
        year, week, _ = today.isocalendar()
        query = """
        MATCH (d:CachedDigest {year: $year, week: $week})
        DELETE d
        """
        async with self._driver.session() as session:
            await session.run(query, year=year, week=week)
```

**Step 2: Run tests to verify they pass**

Run: `cd zettl/api && python -m pytest tests/test_digest_cache_service.py -v`
Expected: All 4 tests PASS

**Step 3: Commit**

```bash
git add zettl/api/app/services/digest_cache_service.py zettl/api/tests/test_digest_cache_service.py
git commit -m "✨feat: add DigestCacheService with Neo4j storage and tests"
```

---

### Task 3: Digest router caching — Write tests

**Files:**
- Modify: `zettl/api/tests/test_digest_router.py`

**Step 1: Add cache-related tests to existing test file**

Add these imports and fixtures at the top (after existing imports):

```python
from app.routers.digest import get_digest_cache_service
```

Update the `client` fixture to also inject a mock cache service:

```python
@pytest.fixture
def mock_cache_service():
    """Create a mock DigestCacheService."""
    mock = MagicMock()
    mock.get_cached_digest = AsyncMock(return_value=None)
    mock.store_digest = AsyncMock()
    mock.invalidate_current_week = AsyncMock()
    return mock


@pytest.fixture
def client(mock_cognee_service, mock_llm_service, mock_cache_service):
    """Create test client with mocked services."""
    app.dependency_overrides[get_cognee_service] = lambda: mock_cognee_service
    app.dependency_overrides[get_llm_service] = lambda: mock_llm_service
    app.dependency_overrides[get_digest_cache_service] = lambda: mock_cache_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

Add these test functions:

```python
def test_digest_returns_cached_when_available(client, mock_cache_service, mock_llm_service):
    from app.models.digest import DigestResponse, TopicSuggestion
    cached = DigestResponse(
        id="cached-123",
        summary="Cached summary",
        suggested_topics=[TopicSuggestion(title="T", reasoning="R", relevant_chunks=[])],
        week_start=datetime(2026, 2, 16),
        week_end=datetime(2026, 2, 22),
        created_at=datetime(2026, 2, 18),
    )
    mock_cache_service.get_cached_digest = AsyncMock(return_value=cached)

    response = client.post("/digest")
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "cached-123"
    assert data["summary"] == "Cached summary"
    mock_llm_service.generate_digest_summary.assert_not_called()


def test_digest_stores_result_on_cache_miss(client, mock_cache_service):
    mock_cache_service.get_cached_digest = AsyncMock(return_value=None)

    response = client.post("/digest")
    assert response.status_code == 201
    mock_cache_service.store_digest.assert_called_once()


def test_digest_force_refresh_bypasses_cache(client, mock_cache_service, mock_llm_service):
    from app.models.digest import DigestResponse, TopicSuggestion
    cached = DigestResponse(
        id="cached-123",
        summary="Cached summary",
        suggested_topics=[],
        week_start=datetime(2026, 2, 16),
        week_end=datetime(2026, 2, 22),
        created_at=datetime(2026, 2, 18),
    )
    mock_cache_service.get_cached_digest = AsyncMock(return_value=cached)

    response = client.post("/digest?force_refresh=true")
    assert response.status_code == 201
    mock_llm_service.generate_digest_summary.assert_called_once()
    mock_cache_service.store_digest.assert_called_once()
```

**Step 2: Run tests to verify new tests fail**

Run: `cd zettl/api && python -m pytest tests/test_digest_router.py -v`
Expected: FAIL — `ImportError: cannot import name 'get_digest_cache_service'`

---

### Task 4: Digest router caching — Implement

**Files:**
- Modify: `zettl/api/app/routers/digest.py`

**Step 1: Update the digest router**

Add import and dependency at top:

```python
from app.services.digest_cache_service import DigestCacheService
```

Add dependency function:

```python
def get_digest_cache_service() -> DigestCacheService:
    """Dependency for DigestCacheService."""
    return DigestCacheService()
```

Replace the `create_digest` endpoint with cache-aware version:

```python
@router.post("/digest", response_model=DigestResponse, status_code=status.HTTP_201_CREATED)
async def create_digest(
    force_refresh: bool = False,
    cognee_service: CogneeService = Depends(get_cognee_service),
    llm_service: LLMService = Depends(get_llm_service),
    cache_service: DigestCacheService = Depends(get_digest_cache_service),
):
    """
    Generate a weekly digest from recent knowledge.
    Returns cached result if available for the current calendar week.
    """
    try:
        now = datetime.now()
        year, week, _ = now.isocalendar()

        # Check cache (unless force refresh requested)
        if not force_refresh:
            cached = await cache_service.get_cached_digest(year, week)
            if cached is not None:
                return cached

        # Calculate date range (last 7 days)
        end_date = now
        start_date = end_date - timedelta(days=7)
        date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

        # Get recent chunks from Cognee
        chunks = await cognee_service.search(
            query="recent learnings and insights",
            search_type="chunks"
        )

        if not chunks:
            return DigestResponse(
                id=str(uuid.uuid4()),
                summary="No new knowledge added this week.",
                suggested_topics=[],
                week_start=start_date,
                week_end=end_date,
                created_at=now,
            )

        # Generate digest summary with LLM
        digest_data = await llm_service.generate_digest_summary(
            chunks=chunks,
            date_range=date_range
        )

        topics = [
            TopicSuggestion(
                title=t.get("title", ""),
                reasoning=t.get("reasoning", ""),
                relevant_chunks=t.get("relevant_chunks", [])
            )
            for t in digest_data.get("topics", [])
        ]

        response = DigestResponse(
            id=str(uuid.uuid4()),
            summary=digest_data.get("summary", ""),
            suggested_topics=topics,
            week_start=start_date,
            week_end=end_date,
            created_at=now,
        )

        # Store in cache
        await cache_service.store_digest(year, week, response)

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create digest: {str(e)}"
        )
```

**Step 2: Run tests to verify they pass**

Run: `cd zettl/api && python -m pytest tests/test_digest_router.py -v`
Expected: All 5 tests PASS (2 existing + 3 new)

**Step 3: Commit**

```bash
git add zettl/api/app/routers/digest.py zettl/api/tests/test_digest_router.py
git commit -m "✨feat: add cache-aware digest endpoint with force_refresh param"
```

---

### Task 5: Notes router invalidation — Write tests

**Files:**
- Modify: `zettl/api/tests/test_notes_router.py`

**Step 1: Add invalidation tests**

Add imports at top:

```python
from app.routers.notes import get_digest_cache_service
```

Add mock cache fixture:

```python
@pytest.fixture
def mock_cache_service():
    """Create a mock DigestCacheService."""
    mock = MagicMock()
    mock.invalidate_current_week = AsyncMock()
    return mock
```

Update client fixture to inject cache service:

```python
@pytest.fixture
def client(mock_cognee_service, mock_cache_service):
    """Create test client with mocked CogneeService."""
    app.dependency_overrides[get_cognee_service] = lambda: mock_cognee_service
    app.dependency_overrides[get_digest_cache_service] = lambda: mock_cache_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

Add test:

```python
def test_create_note_invalidates_digest_cache(client, mock_cache_service):
    response = client.post(
        "/notes",
        json={"content": "New learning about caching"}
    )
    assert response.status_code == 201
    mock_cache_service.invalidate_current_week.assert_called_once()
```

**Step 2: Run tests to verify the new test fails**

Run: `cd zettl/api && python -m pytest tests/test_notes_router.py::test_create_note_invalidates_digest_cache -v`
Expected: FAIL — `ImportError: cannot import name 'get_digest_cache_service' from 'app.routers.notes'`

---

### Task 6: Notes router invalidation — Implement

**Files:**
- Modify: `zettl/api/app/routers/notes.py`

**Step 1: Add cache invalidation to notes router**

Add import at top:

```python
from app.services.digest_cache_service import DigestCacheService
```

Add dependency:

```python
def get_digest_cache_service() -> DigestCacheService:
    """Dependency for DigestCacheService."""
    return DigestCacheService()
```

Update `create_note` to accept and call the cache service:

```python
@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note: NoteCreate,
    cognee_service: CogneeService = Depends(get_cognee_service),
    cache_service: DigestCacheService = Depends(get_digest_cache_service),
):
    """
    Create a new note and process it into the knowledge graph.
    """
    try:
        metadata = {
            "source": note.source.value,
            "tags": ",".join(note.tags) if note.tags else "",
            "created_at": datetime.now().isoformat(),
        }
        if note.source_reference:
            metadata["source_reference"] = note.source_reference

        note_id = await cognee_service.add_note(
            content=note.content,
            metadata=metadata
        )

        # Invalidate cached digest since new knowledge was added
        await cache_service.invalidate_current_week()

        now = datetime.now()
        return NoteResponse(
            id=note_id,
            content=note.content,
            source=note.source,
            tags=note.tags,
            created_at=now,
            updated_at=now,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create note: {str(e)}"
        )
```

**Step 2: Run all tests**

Run: `cd zettl/api && python -m pytest tests/ -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add zettl/api/app/routers/notes.py zettl/api/tests/test_notes_router.py
git commit -m "✨feat: invalidate digest cache when new note is added"
```

---

### Task 7: Add neo4j to explicit dependencies

**Files:**
- Modify: `zettl/api/pyproject.toml`

**Step 1: Add neo4j as an explicit dependency**

The `neo4j` driver is currently a transitive dependency of `cognee[neo4j]`. Since `DigestCacheService` imports it directly, make it explicit.

Add `"neo4j>=5.0.0"` to the `dependencies` list in `pyproject.toml`.

**Step 2: Commit**

```bash
git add zettl/api/pyproject.toml
git commit -m "🔧build: add neo4j as explicit dependency"
```

---

### Task 8: Final verification

**Step 1: Run the full test suite**

Run: `cd zettl/api && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

**Step 2: Commit the design doc and plan**

```bash
git add docs/plans/2026-02-18-digest-caching-design.md docs/plans/2026-02-18-digest-caching-plan.md
git commit -m "📝doc: add digest caching design and implementation plan"
```
