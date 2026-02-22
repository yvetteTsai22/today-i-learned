import json
from datetime import datetime

from neo4j import AsyncGraphDatabase

from app.config import get_settings
from app.models.digest import DigestResponse, TopicSuggestion


class DigestCacheService:
    """Service for caching weekly digests in Neo4j."""

    def __init__(self):
        settings = get_settings()
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def get_cached_digest(self, year: int, week: int) -> DigestResponse | None:
        """Return cached digest for the given ISO year+week, or None."""
        query = (
            "MATCH (d:CachedDigest {year: $year, week: $week}) "
            "RETURN d"
        )
        async with self._driver.session() as session:
            result = await session.run(query, year=year, week=week)
            record = await result.single()

        if record is None:
            return None

        node = record["d"]
        topics = [
            TopicSuggestion(**t) for t in json.loads(node["topics_json"])
        ]
        return DigestResponse(
            id=node["digest_id"],
            summary=node["summary"],
            suggested_topics=topics,
            week_start=datetime.fromisoformat(node["week_start"]),
            week_end=datetime.fromisoformat(node["week_end"]),
            created_at=datetime.fromisoformat(node["created_at"]),
        )

    async def store_digest(
        self, year: int, week: int, digest: DigestResponse
    ) -> None:
        """Store (upsert) a digest for the given ISO year+week."""
        query = (
            "MERGE (d:CachedDigest {year: $year, week: $week}) "
            "SET d.digest_id = $digest_id, "
            "    d.summary = $summary, "
            "    d.topics_json = $topics_json, "
            "    d.week_start = $week_start, "
            "    d.week_end = $week_end, "
            "    d.created_at = $created_at"
        )
        topics_json = json.dumps(
            [t.model_dump(mode="json") for t in digest.suggested_topics]
        )
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
        """Delete the CachedDigest node for the current ISO week."""
        now = datetime.now()
        iso_year, iso_week, _ = now.isocalendar()
        query = (
            "MATCH (d:CachedDigest {year: $year, week: $week}) "
            "DELETE d"
        )
        async with self._driver.session() as session:
            await session.run(query, year=iso_year, week=iso_week)
