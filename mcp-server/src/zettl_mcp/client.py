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
