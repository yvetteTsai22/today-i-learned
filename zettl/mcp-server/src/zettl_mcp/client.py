"""HTTP client for Zettl API."""

import os
from typing import Any

import httpx


class ZettlAPIError(Exception):
    """Error communicating with Zettl API."""
    pass


class ZettlClient:
    """Async HTTP client for communicating with the Zettl API."""

    DEFAULT_TIMEOUT = 30.0
    LONG_TIMEOUT = 120.0  # For operations that trigger cognify/LLM processing

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
            timeout=self.DEFAULT_TIMEOUT,
        )

    async def _request(
        self,
        method: str,
        path: str,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make HTTP request with error handling.

        Args:
            method: HTTP method (get, post, etc.)
            path: API endpoint path
            timeout: Per-request timeout override in seconds
            **kwargs: Additional arguments for httpx request

        Returns:
            Parsed JSON response

        Raises:
            ZettlAPIError: If request fails
        """
        effective_timeout = timeout or self.DEFAULT_TIMEOUT
        try:
            request_method = getattr(self._http, method)
            response = await request_method(
                path, timeout=effective_timeout, **kwargs
            )
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
            raise ZettlAPIError(
                f"Zettl API timeout after {int(effective_timeout)}s"
            )

    async def health_check(self) -> dict[str, Any]:
        """Check API health status."""
        return await self._request("get", "/health")

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
        return await self._request(
            "post", "/notes", timeout=self.LONG_TIMEOUT, json=payload
        )

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

    async def generate_digest(
        self, force_refresh: bool = False
    ) -> dict[str, Any]:
        """Generate weekly digest with topic suggestions.

        Args:
            force_refresh: Bypass cache and regenerate from LLM

        Returns:
            Digest response with summary and suggested topics
        """
        params = {"force_refresh": "true"} if force_refresh else {}
        return await self._request(
            "post", "/digest", timeout=self.LONG_TIMEOUT, params=params
        )

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
        return await self._request(
            "post", "/digest/content", timeout=self.LONG_TIMEOUT, json=payload
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()
