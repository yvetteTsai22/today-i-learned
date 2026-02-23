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

    async def get_graph(self) -> dict:
        """Return all nodes and relationships for graph visualization."""
        async with self._driver.session() as session:
            # Get all nodes (limit to prevent overwhelming the UI)
            node_result = await session.run(
                "MATCH (n) "
                "WHERE NOT n:CachedDigest "
                "RETURN elementId(n) AS id, labels(n)[0] AS label, "
                "       coalesce(n.text, n.name, n.content, '') AS content "
                "LIMIT 200"
            )
            nodes = [
                {
                    "id": record["id"],
                    "label": record["label"],
                    "content": record["content"][:100],
                }
                async for record in node_result
            ]

            # Get relationships only between the fetched nodes
            node_ids = [n["id"] for n in nodes]
            edge_result = await session.run(
                "MATCH (a)-[r]->(b) "
                "WHERE elementId(a) IN $node_ids AND elementId(b) IN $node_ids "
                "RETURN elementId(a) AS source, elementId(b) AS target, type(r) AS type "
                "LIMIT 500",
                node_ids=node_ids,
            )
            edges = [
                {
                    "source": record["source"],
                    "target": record["target"],
                    "type": record["type"],
                }
                async for record in edge_result
            ]

        return {"nodes": nodes, "edges": edges}
