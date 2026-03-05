from datetime import datetime, timedelta, timezone

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
                "WHERE NOT n:CachedDigest AND NOT n:CachedSearch "
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

    async def get_activity(self, limit: int = 20) -> list[dict]:
        """Return recent activity across notes, searches, and digests."""
        cypher = (
            "CALL { "
            "  MATCH (n:DocumentChunk) "
            "  WHERE n.created_at IS NOT NULL "
            "  RETURN 'note' AS type, "
            "         n.created_at AS ts, "
            "         'Note captured' AS label_text, "
            "         substring(coalesce(n.text, ''), 0, 80) AS preview_text "
            "  UNION ALL "
            "  MATCH (d:CachedDigest) "
            "  WHERE d.created_at IS NOT NULL "
            "  RETURN 'digest' AS type, "
            "         d.created_at AS ts, "
            "         'Digest generated' AS label_text, "
            "         '' AS preview_text "
            "  UNION ALL "
            "  MATCH (s:CachedSearch) "
            "  WHERE s.created_at IS NOT NULL "
            "  RETURN 'search' AS type, "
            "         s.created_at AS ts, "
            "         'Searched: \"' + s.query + '\"' AS label_text, "
            "         coalesce(s.preview, '') AS preview_text "
            "} "
            "RETURN type, ts, label_text, preview_text "
            "ORDER BY ts DESC "
            "LIMIT $limit"
        )
        async with self._driver.session() as session:
            result = await session.run(cypher, limit=limit)
            items = []
            async for record in result:
                ts = record["ts"]
                if isinstance(ts, int):
                    ts = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()
                else:
                    ts = str(ts) if ts is not None else ""
                items.append({
                    "type": record["type"],
                    "label": record["label_text"],
                    "timestamp": ts,
                    "preview": record["preview_text"] if record["preview_text"] else None,
                })
            return items
