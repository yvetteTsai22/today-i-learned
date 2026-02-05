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
