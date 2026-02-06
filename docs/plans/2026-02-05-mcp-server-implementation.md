# Zettl MCP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an MCP server that exposes Zettl's knowledge management API to AI agents via four tools: add_note, search_knowledge, generate_digest, generate_content.

**Architecture:** HTTP client pattern — MCP server calls existing FastAPI endpoints. FastMCP framework for simple decorator-based tool registration. Async httpx for API communication.

**Tech Stack:** Python 3.11+, mcp SDK (FastMCP), httpx, pytest, pytest-anyio

---

## Task 1: Project Scaffolding

**Files:**
- Create: `mcp-server/pyproject.toml`
- Create: `mcp-server/src/zettl_mcp/__init__.py`
- Create: `mcp-server/README.md`
- Create: `mcp-server/TODO.md`

**Step 1: Create directory structure**

```bash
mkdir -p zettl/mcp-server/src/zettl_mcp
mkdir -p zettl/mcp-server/tests
```

**Step 2: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "zettl-mcp"
version = "0.1.0"
description = "MCP server for Zettl knowledge management API"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-anyio>=0.0.0",
    "inline-snapshot>=0.10.0",
]

[tool.hatch.build.targets.wheel]
packages = ["src/zettl_mcp"]
```

**Step 3: Create __init__.py**

```python
"""Zettl MCP Server - Expose knowledge management API to AI agents."""

__version__ = "0.1.0"
```

**Step 4: Create README.md**

```markdown
# Zettl MCP Server

MCP server that exposes the Zettl knowledge management API to AI agents.

## Installation

```bash
cd zettl/mcp-server
pip install -e ".[dev]"
```

## Usage

### Run standalone (testing)

```bash
python -m zettl_mcp
```

### Claude Code configuration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "zettl": {
      "command": "python",
      "args": ["-m", "zettl_mcp"],
      "env": {
        "ZETTL_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Tools

- `add_note` - Add a note to your knowledge graph
- `search_knowledge` - Semantic search across your knowledge
- `generate_digest` - Create weekly summary with topic suggestions
- `generate_content` - Generate content drafts for a topic
```

**Step 5: Create TODO.md**

```markdown
# Zettl MCP Server Roadmap

## Phase 1: Tools (Current)
- [x] Project scaffolding
- [ ] HTTP client for Zettl API
- [ ] add_note tool
- [ ] search_knowledge tool
- [ ] generate_digest tool
- [ ] generate_content tool

## Phase 2: Resources
- [ ] zettl://health — API health status
- [ ] zettl://recent-notes — Last N notes added
- [ ] zettl://digest/latest — Most recent digest

## Phase 3: Prompts
- [ ] explore-topic — "What have I learned about {topic}?"
- [ ] weekly-review — "Summarize my week and suggest content"
- [ ] content-idea — "Generate content ideas from recent notes"
```

**Step 6: Commit**

```bash
git add mcp-server/
git commit -m "feat(mcp): scaffold MCP server project structure"
```

---

## Task 2: HTTP Client - Health Check

**Files:**
- Create: `mcp-server/src/zettl_mcp/client.py`
- Create: `mcp-server/tests/test_client.py`
- Create: `mcp-server/tests/conftest.py`

**Step 1: Create conftest.py with shared fixtures**

```python
"""Shared test fixtures for Zettl MCP tests."""

import pytest


@pytest.fixture
def anyio_backend():
    """Use asyncio as the async backend for tests."""
    return "asyncio"
```

**Step 2: Write the failing test for health check**

```python
"""Tests for ZettlClient."""

import pytest
from unittest.mock import AsyncMock, patch

from zettl_mcp.client import ZettlClient


@pytest.mark.anyio
async def test_health_check_success():
    """Client returns health status when API is healthy."""
    client = ZettlClient(base_url="http://test:8000")

    with patch.object(client, "_http") as mock_http:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_http.get = AsyncMock(return_value=mock_response)

        result = await client.health_check()

        assert result == {"status": "healthy"}
        mock_http.get.assert_called_once_with("/health")
```

**Step 3: Run test to verify it fails**

Run: `cd zettl/mcp-server && pytest tests/test_client.py::test_health_check_success -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'zettl_mcp'"

**Step 4: Write minimal client implementation**

```python
"""HTTP client for Zettl API."""

import os
from typing import Any

import httpx


class ZettlClient:
    """Async HTTP client for communicating with the Zettl API."""

    def __init__(self, base_url: str | None = None):
        """Initialize client with API base URL.

        Args:
            base_url: Zettl API URL. Defaults to ZETTL_API_URL env var
                     or http://localhost:8000.
        """
        self.base_url = base_url or os.getenv(
            "ZETTL_API_URL", "http://localhost:8000"
        )
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
        )

    async def health_check(self) -> dict[str, Any]:
        """Check API health status.

        Returns:
            Health status dict from API.

        Raises:
            ZettlAPIError: If API request fails.
        """
        response = await self._http.get("/health")
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()
```

**Step 5: Run test to verify it passes**

Run: `cd zettl/mcp-server && pip install -e ".[dev]" && pytest tests/test_client.py::test_health_check_success -v`
Expected: PASS

**Step 6: Commit**

```bash
git add mcp-server/src/zettl_mcp/client.py mcp-server/tests/
git commit -m "feat(mcp): add ZettlClient with health check"
```

---

## Task 3: HTTP Client - Error Handling

**Files:**
- Modify: `mcp-server/src/zettl_mcp/client.py`
- Modify: `mcp-server/tests/test_client.py`

**Step 1: Write failing tests for error scenarios**

Add to `tests/test_client.py`:

```python
@pytest.mark.anyio
async def test_health_check_network_error():
    """Client returns friendly message when API unreachable."""
    client = ZettlClient(base_url="http://test:8000")

    with patch.object(client, "_http") as mock_http:
        mock_http.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

        with pytest.raises(ZettlAPIError) as exc_info:
            await client.health_check()

        assert "Cannot reach Zettl API" in str(exc_info.value)


@pytest.mark.anyio
async def test_health_check_server_error():
    """Client wraps 5xx errors with context."""
    client = ZettlClient(base_url="http://test:8000")

    with patch.object(client, "_http") as mock_http:
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=AsyncMock(), response=mock_response
        )
        mock_http.get = AsyncMock(return_value=mock_response)

        with pytest.raises(ZettlAPIError) as exc_info:
            await client.health_check()

        assert "Zettl API error" in str(exc_info.value)
```

Also add import at top:
```python
import httpx
from zettl_mcp.client import ZettlClient, ZettlAPIError
```

**Step 2: Run tests to verify they fail**

Run: `cd zettl/mcp-server && pytest tests/test_client.py -v`
Expected: FAIL with "ImportError: cannot import name 'ZettlAPIError'"

**Step 3: Add error handling to client**

Update `client.py`:

```python
"""HTTP client for Zettl API."""

import os
from typing import Any

import httpx


class ZettlAPIError(Exception):
    """Error communicating with Zettl API."""
    pass


class ZettlClient:
    """Async HTTP client for communicating with the Zettl API."""

    def __init__(self, base_url: str | None = None):
        """Initialize client with API base URL.

        Args:
            base_url: Zettl API URL. Defaults to ZETTL_API_URL env var
                     or http://localhost:8000.
        """
        self.base_url = base_url or os.getenv(
            "ZETTL_API_URL", "http://localhost:8000"
        )
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
        )

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make HTTP request with error handling.

        Args:
            method: HTTP method (get, post, etc.)
            path: API endpoint path
            **kwargs: Additional arguments for httpx request

        Returns:
            Parsed JSON response

        Raises:
            ZettlAPIError: If request fails
        """
        try:
            request_method = getattr(self._http, method)
            response = await request_method(path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            raise ZettlAPIError(f"Cannot reach Zettl API at {self.base_url}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                raise ZettlAPIError(f"Zettl API error: {e.response.status_code}")
            # Re-raise 4xx for validation errors
            raise ZettlAPIError(f"Request failed: {e.response.text}")
        except httpx.TimeoutException:
            raise ZettlAPIError(f"Zettl API timeout after 30s")

    async def health_check(self) -> dict[str, Any]:
        """Check API health status."""
        return await self._request("get", "/health")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()
```

**Step 4: Update tests to use _request method**

Update `tests/test_client.py`:

```python
"""Tests for ZettlClient."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

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
```

**Step 5: Run tests to verify they pass**

Run: `cd zettl/mcp-server && pytest tests/test_client.py -v`
Expected: All 3 tests PASS

**Step 6: Commit**

```bash
git add mcp-server/src/zettl_mcp/client.py mcp-server/tests/test_client.py
git commit -m "feat(mcp): add error handling to ZettlClient"
```

---

## Task 4: HTTP Client - add_note Method

**Files:**
- Modify: `mcp-server/src/zettl_mcp/client.py`
- Modify: `mcp-server/tests/test_client.py`

**Step 1: Write failing test**

Add to `tests/test_client.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd zettl/mcp-server && pytest tests/test_client.py::test_add_note_success -v`
Expected: FAIL with "AttributeError: 'ZettlClient' object has no attribute 'add_note'"

**Step 3: Implement add_note method**

Add to `client.py` in the ZettlClient class:

```python
    async def add_note(
        self,
        content: str,
        tags: list[str] | None = None,
        source: str = "agent",
    ) -> dict[str, Any]:
        """Add a note to the knowledge graph.

        Args:
            content: Note content text
            tags: Optional list of tags
            source: Note source (defaults to "agent" for MCP)

        Returns:
            Created note response from API
        """
        payload = {
            "content": content,
            "source": source,
            "tags": tags or [],
        }
        return await self._request("post", "/notes", json=payload)
```

**Step 4: Run test to verify it passes**

Run: `cd zettl/mcp-server && pytest tests/test_client.py::test_add_note_success -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/src/zettl_mcp/client.py mcp-server/tests/test_client.py
git commit -m "feat(mcp): add add_note method to ZettlClient"
```

---

## Task 5: HTTP Client - search Method

**Files:**
- Modify: `mcp-server/src/zettl_mcp/client.py`
- Modify: `mcp-server/tests/test_client.py`

**Step 1: Write failing test**

Add to `tests/test_client.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd zettl/mcp-server && pytest tests/test_client.py::test_search_success -v`
Expected: FAIL with "AttributeError: 'ZettlClient' object has no attribute 'search'"

**Step 3: Implement search method**

Add to `client.py` in the ZettlClient class:

```python
    async def search(
        self,
        query: str,
        search_type: str = "graph_completion",
    ) -> dict[str, Any]:
        """Search the knowledge graph.

        Args:
            query: Search query text
            search_type: Type of search ("graph_completion" or "chunks")

        Returns:
            Search results from API
        """
        payload = {
            "query": query,
            "search_type": search_type,
        }
        return await self._request("post", "/search", json=payload)
```

**Step 4: Run test to verify it passes**

Run: `cd zettl/mcp-server && pytest tests/test_client.py::test_search_success -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/src/zettl_mcp/client.py mcp-server/tests/test_client.py
git commit -m "feat(mcp): add search method to ZettlClient"
```

---

## Task 6: HTTP Client - generate_digest Method

**Files:**
- Modify: `mcp-server/src/zettl_mcp/client.py`
- Modify: `mcp-server/tests/test_client.py`

**Step 1: Write failing test**

Add to `tests/test_client.py`:

```python
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
        mock_post.assert_called_once_with("/digest")
```

**Step 2: Run test to verify it fails**

Run: `cd zettl/mcp-server && pytest tests/test_client.py::test_generate_digest_success -v`
Expected: FAIL with "AttributeError: 'ZettlClient' object has no attribute 'generate_digest'"

**Step 3: Implement generate_digest method**

Add to `client.py` in the ZettlClient class:

```python
    async def generate_digest(self) -> dict[str, Any]:
        """Generate weekly digest with topic suggestions.

        Returns:
            Digest response with summary and suggested topics
        """
        return await self._request("post", "/digest")
```

**Step 4: Run test to verify it passes**

Run: `cd zettl/mcp-server && pytest tests/test_client.py::test_generate_digest_success -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/src/zettl_mcp/client.py mcp-server/tests/test_client.py
git commit -m "feat(mcp): add generate_digest method to ZettlClient"
```

---

## Task 7: HTTP Client - generate_content Method

**Files:**
- Modify: `mcp-server/src/zettl_mcp/client.py`
- Modify: `mcp-server/tests/test_client.py`

**Step 1: Write failing test**

Add to `tests/test_client.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd zettl/mcp-server && pytest tests/test_client.py::test_generate_content_success -v`
Expected: FAIL with "AttributeError: 'ZettlClient' object has no attribute 'generate_content'"

**Step 3: Implement generate_content method**

Add to `client.py` in the ZettlClient class:

```python
    async def generate_content(
        self,
        topic: str,
        source_chunks: list[str],
        formats: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate content drafts for a topic.

        Args:
            topic: Content topic
            source_chunks: Relevant knowledge chunks
            formats: Output formats (blog, linkedin, x_thread, video_script)

        Returns:
            Generated content in requested formats
        """
        payload = {
            "topic": topic,
            "source_chunks": source_chunks,
            "formats": formats or ["blog", "linkedin"],
        }
        return await self._request("post", "/digest/content", json=payload)
```

**Step 4: Run test to verify it passes**

Run: `cd zettl/mcp-server && pytest tests/test_client.py::test_generate_content_success -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/src/zettl_mcp/client.py mcp-server/tests/test_client.py
git commit -m "feat(mcp): add generate_content method to ZettlClient"
```

---

## Task 8: MCP Server - Basic Setup

**Files:**
- Create: `mcp-server/src/zettl_mcp/server.py`
- Create: `mcp-server/src/zettl_mcp/__main__.py`
- Create: `mcp-server/tests/test_server.py`

**Step 1: Write failing test for server initialization**

Create `tests/test_server.py`:

```python
"""Tests for MCP server."""

import pytest
from mcp.client.session import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session

from zettl_mcp.server import mcp


@pytest.mark.anyio
async def test_server_lists_tools():
    """Server exposes expected tools."""
    async with create_connected_server_and_client_session(mcp._mcp_server) as session:
        tools = await session.list_tools()
        tool_names = [t.name for t in tools.tools]

        assert "add_note" in tool_names
        assert "search_knowledge" in tool_names
        assert "generate_digest" in tool_names
        assert "generate_content" in tool_names
```

**Step 2: Run test to verify it fails**

Run: `cd zettl/mcp-server && pytest tests/test_server.py::test_server_lists_tools -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'zettl_mcp.server'"

**Step 3: Create basic server with tool stubs**

Create `src/zettl_mcp/server.py`:

```python
"""MCP server for Zettl knowledge management API."""

from mcp.server.fastmcp import FastMCP

from zettl_mcp.client import ZettlClient

# Initialize MCP server
mcp = FastMCP(
    "Zettl",
    dependencies=["httpx>=0.27.0"],
)

# Client instance (lazy initialization)
_client: ZettlClient | None = None


def get_client() -> ZettlClient:
    """Get or create the Zettl API client."""
    global _client
    if _client is None:
        _client = ZettlClient()
    return _client


@mcp.tool()
async def add_note(
    content: str,
    tags: list[str] | None = None,
    source: str = "agent",
) -> str:
    """Add a note to your Zettl knowledge graph.

    Args:
        content: The note content to add
        tags: Optional tags to categorize the note
        source: Origin of the note (defaults to "agent")
    """
    # Stub - will implement in next task
    return "Not implemented"


@mcp.tool()
async def search_knowledge(
    query: str,
    search_type: str = "graph_completion",
) -> str:
    """Search your knowledge graph semantically.

    Args:
        query: What to search for
        search_type: "graph_completion" for connected insights or "chunks" for raw matches
    """
    # Stub - will implement in next task
    return "Not implemented"


@mcp.tool()
async def generate_digest() -> str:
    """Generate a weekly digest with topic suggestions from your recent knowledge."""
    # Stub - will implement in next task
    return "Not implemented"


@mcp.tool()
async def generate_content(
    topic: str,
    source_chunks: list[str],
    formats: list[str] | None = None,
) -> str:
    """Generate content drafts for a topic from your knowledge.

    Args:
        topic: The topic to write about
        source_chunks: Relevant knowledge chunks to use as source
        formats: Output formats (blog, linkedin, x_thread, video_script)
    """
    # Stub - will implement in next task
    return "Not implemented"
```

Create `src/zettl_mcp/__main__.py`:

```python
"""Entry point for running Zettl MCP server."""

from zettl_mcp.server import mcp

if __name__ == "__main__":
    mcp.run()
```

**Step 4: Run test to verify it passes**

Run: `cd zettl/mcp-server && pytest tests/test_server.py::test_server_lists_tools -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/src/zettl_mcp/server.py mcp-server/src/zettl_mcp/__main__.py mcp-server/tests/test_server.py
git commit -m "feat(mcp): add MCP server with tool stubs"
```

---

## Task 9: MCP Server - add_note Tool Implementation

**Files:**
- Modify: `mcp-server/src/zettl_mcp/server.py`
- Modify: `mcp-server/tests/test_server.py`

**Step 1: Write failing test**

Add to `tests/test_server.py`:

```python
from unittest.mock import AsyncMock, patch


@pytest.mark.anyio
async def test_add_note_tool():
    """add_note tool creates note and returns confirmation."""
    mock_client = AsyncMock()
    mock_client.add_note.return_value = {
        "id": "note-abc123",
        "content": "Test note content",
        "source": "agent",
        "tags": ["test"],
    }

    with patch("zettl_mcp.server.get_client", return_value=mock_client):
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            result = await session.call_tool("add_note", {
                "content": "Test note content",
                "tags": ["test"],
            })

            # Result should be a success message
            assert len(result.content) == 1
            assert "note-abc123" in result.content[0].text
            mock_client.add_note.assert_called_once_with(
                content="Test note content",
                tags=["test"],
                source="agent",
            )
```

**Step 2: Run test to verify it fails**

Run: `cd zettl/mcp-server && pytest tests/test_server.py::test_add_note_tool -v`
Expected: FAIL (returns "Not implemented")

**Step 3: Implement add_note tool**

Update `add_note` in `server.py`:

```python
@mcp.tool()
async def add_note(
    content: str,
    tags: list[str] | None = None,
    source: str = "agent",
) -> str:
    """Add a note to your Zettl knowledge graph.

    Args:
        content: The note content to add
        tags: Optional tags to categorize the note
        source: Origin of the note (defaults to "agent")
    """
    client = get_client()
    try:
        result = await client.add_note(
            content=content,
            tags=tags,
            source=source,
        )
        return f"Note added (id: {result['id']})"
    except Exception as e:
        return f"Failed to add note: {e}"
```

**Step 4: Run test to verify it passes**

Run: `cd zettl/mcp-server && pytest tests/test_server.py::test_add_note_tool -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/src/zettl_mcp/server.py mcp-server/tests/test_server.py
git commit -m "feat(mcp): implement add_note tool"
```

---

## Task 10: MCP Server - search_knowledge Tool Implementation

**Files:**
- Modify: `mcp-server/src/zettl_mcp/server.py`
- Modify: `mcp-server/tests/test_server.py`

**Step 1: Write failing test**

Add to `tests/test_server.py`:

```python
@pytest.mark.anyio
async def test_search_knowledge_tool():
    """search_knowledge tool returns formatted results."""
    mock_client = AsyncMock()
    mock_client.search.return_value = {
        "results": ["First insight about AI", "Second insight about testing"],
        "query": "AI testing",
    }

    with patch("zettl_mcp.server.get_client", return_value=mock_client):
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            result = await session.call_tool("search_knowledge", {
                "query": "AI testing",
            })

            assert "First insight about AI" in result.content[0].text
            assert "Second insight about testing" in result.content[0].text


@pytest.mark.anyio
async def test_search_knowledge_empty_results():
    """search_knowledge handles empty results gracefully."""
    mock_client = AsyncMock()
    mock_client.search.return_value = {
        "results": [],
        "query": "nonexistent topic",
    }

    with patch("zettl_mcp.server.get_client", return_value=mock_client):
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            result = await session.call_tool("search_knowledge", {
                "query": "nonexistent topic",
            })

            assert "No results found" in result.content[0].text
```

**Step 2: Run tests to verify they fail**

Run: `cd zettl/mcp-server && pytest tests/test_server.py::test_search_knowledge_tool tests/test_server.py::test_search_knowledge_empty_results -v`
Expected: FAIL

**Step 3: Implement search_knowledge tool**

Update `search_knowledge` in `server.py`:

```python
@mcp.tool()
async def search_knowledge(
    query: str,
    search_type: str = "graph_completion",
) -> str:
    """Search your knowledge graph semantically.

    Args:
        query: What to search for
        search_type: "graph_completion" for connected insights or "chunks" for raw matches
    """
    client = get_client()
    try:
        result = await client.search(query=query, search_type=search_type)

        if not result.get("results"):
            return "No results found."

        return "\n\n".join(result["results"])
    except Exception as e:
        return f"Search failed: {e}"
```

**Step 4: Run tests to verify they pass**

Run: `cd zettl/mcp-server && pytest tests/test_server.py::test_search_knowledge_tool tests/test_server.py::test_search_knowledge_empty_results -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/src/zettl_mcp/server.py mcp-server/tests/test_server.py
git commit -m "feat(mcp): implement search_knowledge tool"
```

---

## Task 11: MCP Server - generate_digest Tool Implementation

**Files:**
- Modify: `mcp-server/src/zettl_mcp/server.py`
- Modify: `mcp-server/tests/test_server.py`

**Step 1: Write failing test**

Add to `tests/test_server.py`:

```python
@pytest.mark.anyio
async def test_generate_digest_tool():
    """generate_digest tool returns formatted summary and topics."""
    mock_client = AsyncMock()
    mock_client.generate_digest.return_value = {
        "id": "digest-123",
        "summary": "This week you learned about AI testing patterns.",
        "suggested_topics": [
            {"title": "TDD for AI", "reasoning": "Multiple notes on testing"},
            {"title": "Prompt Engineering", "reasoning": "Growing interest"},
        ],
    }

    with patch("zettl_mcp.server.get_client", return_value=mock_client):
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            result = await session.call_tool("generate_digest", {})

            text = result.content[0].text
            assert "AI testing patterns" in text
            assert "TDD for AI" in text
            assert "Prompt Engineering" in text
```

**Step 2: Run test to verify it fails**

Run: `cd zettl/mcp-server && pytest tests/test_server.py::test_generate_digest_tool -v`
Expected: FAIL

**Step 3: Implement generate_digest tool with formatting**

Update `generate_digest` in `server.py`:

```python
@mcp.tool()
async def generate_digest() -> str:
    """Generate a weekly digest with topic suggestions from your recent knowledge."""
    client = get_client()
    try:
        result = await client.generate_digest()

        # Format the digest nicely
        output = ["## Weekly Digest\n"]
        output.append(result.get("summary", "No summary available."))

        topics = result.get("suggested_topics", [])
        if topics:
            output.append("\n\n## Suggested Content Topics\n")
            for i, topic in enumerate(topics, 1):
                output.append(f"{i}. **{topic.get('title', 'Untitled')}**")
                if topic.get("reasoning"):
                    output.append(f"   - {topic['reasoning']}")

        return "\n".join(output)
    except Exception as e:
        return f"Failed to generate digest: {e}"
```

**Step 4: Run test to verify it passes**

Run: `cd zettl/mcp-server && pytest tests/test_server.py::test_generate_digest_tool -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/src/zettl_mcp/server.py mcp-server/tests/test_server.py
git commit -m "feat(mcp): implement generate_digest tool"
```

---

## Task 12: MCP Server - generate_content Tool Implementation

**Files:**
- Modify: `mcp-server/src/zettl_mcp/server.py`
- Modify: `mcp-server/tests/test_server.py`

**Step 1: Write failing test**

Add to `tests/test_server.py`:

```python
@pytest.mark.anyio
async def test_generate_content_tool():
    """generate_content tool returns formatted content drafts."""
    mock_client = AsyncMock()
    mock_client.generate_content.return_value = {
        "topic": "AI Testing",
        "blog": "# Testing AI Systems\n\nWriting tests for AI...",
        "linkedin": "Excited to share insights on AI testing!",
    }

    with patch("zettl_mcp.server.get_client", return_value=mock_client):
        async with create_connected_server_and_client_session(mcp._mcp_server) as session:
            result = await session.call_tool("generate_content", {
                "topic": "AI Testing",
                "source_chunks": ["chunk 1", "chunk 2"],
                "formats": ["blog", "linkedin"],
            })

            text = result.content[0].text
            assert "Blog" in text
            assert "LinkedIn" in text
            assert "Testing AI Systems" in text
```

**Step 2: Run test to verify it fails**

Run: `cd zettl/mcp-server && pytest tests/test_server.py::test_generate_content_tool -v`
Expected: FAIL

**Step 3: Implement generate_content tool with formatting**

Update `generate_content` in `server.py`:

```python
@mcp.tool()
async def generate_content(
    topic: str,
    source_chunks: list[str],
    formats: list[str] | None = None,
) -> str:
    """Generate content drafts for a topic from your knowledge.

    Args:
        topic: The topic to write about
        source_chunks: Relevant knowledge chunks to use as source
        formats: Output formats (blog, linkedin, x_thread, video_script)
    """
    client = get_client()
    try:
        result = await client.generate_content(
            topic=topic,
            source_chunks=source_chunks,
            formats=formats,
        )

        # Format output with clear sections
        output = [f"# Content Drafts: {result.get('topic', topic)}\n"]

        format_labels = {
            "blog": "Blog Post",
            "linkedin": "LinkedIn",
            "x_thread": "X Thread",
            "video_script": "Video Script",
        }

        for key, label in format_labels.items():
            if key in result and result[key]:
                output.append(f"\n## {label}\n")
                output.append(result[key])

        return "\n".join(output)
    except Exception as e:
        return f"Failed to generate content: {e}"
```

**Step 4: Run test to verify it passes**

Run: `cd zettl/mcp-server && pytest tests/test_server.py::test_generate_content_tool -v`
Expected: PASS

**Step 5: Commit**

```bash
git add mcp-server/src/zettl_mcp/server.py mcp-server/tests/test_server.py
git commit -m "feat(mcp): implement generate_content tool"
```

---

## Task 13: Final Integration & Cleanup

**Files:**
- Modify: `mcp-server/TODO.md`
- Modify: `mcp-server/src/zettl_mcp/__init__.py`

**Step 1: Run full test suite**

Run: `cd zettl/mcp-server && pytest -v`
Expected: All tests PASS

**Step 2: Update TODO.md with completed items**

```markdown
# Zettl MCP Server Roadmap

## Phase 1: Tools (Complete)
- [x] Project scaffolding
- [x] HTTP client for Zettl API
- [x] add_note tool
- [x] search_knowledge tool
- [x] generate_digest tool
- [x] generate_content tool

## Phase 2: Resources
- [ ] zettl://health — API health status
- [ ] zettl://recent-notes — Last N notes added
- [ ] zettl://digest/latest — Most recent digest

## Phase 3: Prompts
- [ ] explore-topic — "What have I learned about {topic}?"
- [ ] weekly-review — "Summarize my week and suggest content"
- [ ] content-idea — "Generate content ideas from recent notes"
```

**Step 3: Update __init__.py exports**

```python
"""Zettl MCP Server - Expose knowledge management API to AI agents."""

from zettl_mcp.server import mcp
from zettl_mcp.client import ZettlClient, ZettlAPIError

__version__ = "0.1.0"
__all__ = ["mcp", "ZettlClient", "ZettlAPIError"]
```

**Step 4: Final commit**

```bash
git add mcp-server/
git commit -m "feat(mcp): complete Phase 1 - all tools implemented"
```

---

## Summary

| Task | Description | Tests |
|------|-------------|-------|
| 1 | Project scaffolding | - |
| 2 | Client health check | 1 |
| 3 | Client error handling | 2 |
| 4 | Client add_note | 1 |
| 5 | Client search | 1 |
| 6 | Client generate_digest | 1 |
| 7 | Client generate_content | 1 |
| 8 | Server setup with stubs | 1 |
| 9 | add_note tool | 1 |
| 10 | search_knowledge tool | 2 |
| 11 | generate_digest tool | 1 |
| 12 | generate_content tool | 1 |
| 13 | Integration & cleanup | - |

**Total: 13 tasks, ~13 tests**
