from datetime import datetime, timedelta

from neo4j import AsyncGraphDatabase

from app.config import get_settings


class StatsService:
    """Service for querying knowledge graph statistics from Neo4j."""

    def __init__(self):
        settings = get_settings()
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def get_stats(self) -> dict:
        """Return dashboard KPI stats."""
        async with self._driver.session() as session:
            # Total notes (DocumentChunk nodes created by Cognee)
            result = await session.run(
                "MATCH (n:DocumentChunk) RETURN count(n) AS count"
            )
            record = await result.single()
            total_notes = record["count"] if record else 0

            # Topics (distinct non-chunk, non-cache node labels)
            result = await session.run(
                "CALL db.labels() YIELD label "
                "WHERE label <> 'DocumentChunk' AND label <> 'CachedDigest' "
                "RETURN count(label) AS count"
            )
            record = await result.single()
            topics = record["count"] if record else 0

            # Connections (all relationships)
            result = await session.run(
                "MATCH ()-[r]->() RETURN count(r) AS count"
            )
            record = await result.single()
            connections = record["count"] if record else 0

            # Notes added this week (chunks with recent created_at in metadata)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            result = await session.run(
                "MATCH (n:DocumentChunk) "
                "WHERE n.created_at >= $week_ago "
                "RETURN count(n) AS count",
                week_ago=week_ago,
            )
            record = await result.single()
            this_week = record["count"] if record else 0

        return {
            "notes": total_notes,
            "topics": topics,
            "connections": connections,
            "this_week": this_week,
        }
