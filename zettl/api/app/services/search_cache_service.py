import json
from datetime import datetime, timedelta

from neo4j import AsyncGraphDatabase

from app.config import get_settings


class SearchCacheService:
    """Service for caching search results in Neo4j with 24-hour TTL."""

    def __init__(self):
        settings = get_settings()
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def get_cached_search(self, query: str) -> list[dict] | None:
        """Return cached search results for query, or None if expired/missing."""
        normalized = query.strip().lower()
        cypher = (
            "MATCH (s:CachedSearch {query: $query}) "
            "WHERE s.expires_at > $now "
            "RETURN s"
        )
        async with self._driver.session() as session:
            result = await session.run(
                cypher, query=normalized, now=datetime.now().isoformat()
            )
            record = await result.single()

        if record is None:
            return None

        return json.loads(record["s"]["results_json"])

    async def store_search(self, query: str, results: list[dict]) -> None:
        """Store (upsert) search results with 24-hour expiry."""
        normalized = query.strip().lower()
        now = datetime.now()
        preview = results[0]["content"][:80] if results else ""
        cypher = (
            "MERGE (s:CachedSearch {query: $query}) "
            "SET s.results_json = $results_json, "
            "    s.preview = $preview, "
            "    s.created_at = $created_at, "
            "    s.expires_at = $expires_at"
        )
        async with self._driver.session() as session:
            await session.run(
                cypher,
                query=normalized,
                results_json=json.dumps(results),
                preview=preview,
                created_at=now.isoformat(),
                expires_at=(now + timedelta(hours=24)).isoformat(),
            )
