import cognee
from cognee.modules.search.types import SearchType
from datetime import datetime
import uuid
import re
from typing import Any, TypedDict


class ChunkResult(TypedDict):
    id: str
    content: str
    source: str
    tags: list[str]
    created_at: str


def is_cognee_no_data_error(exc: Exception) -> bool:
    """Return True for Cognee's 'no data' errors (raised when the graph is empty)."""
    return "NoDataError" in type(exc).__name__ or "No data found" in str(exc)


class CogneeService:
    """Service for interacting with Cognee knowledge graph."""

    DEFAULT_DATASET = "zettl_notes"

    @staticmethod
    def _enrich_content(content: str, metadata: dict | None) -> str:
        if not metadata:
            return content
        meta_str = " | ".join(f"{k}: {v}" for k, v in metadata.items())
        return f"[{meta_str}]\n{content}"

    async def add_note(
        self,
        content: str,
        dataset_name: str | None = None,
        metadata: dict | None = None
    ) -> str:
        """
        Stage a note in Cognee's data store (fast step).

        Returns the note ID. Call cognify_dataset() separately as a
        background task to process the note into the knowledge graph.
        """
        dataset = dataset_name or self.DEFAULT_DATASET
        note_id = str(uuid.uuid4())

        await cognee.add([self._enrich_content(content, metadata)], dataset_name=dataset)

        return note_id

    async def cognify_dataset(self, dataset_name: str | None = None) -> None:
        """Process staged notes into the knowledge graph (slow LLM step)."""
        dataset = dataset_name or self.DEFAULT_DATASET
        await cognee.cognify([dataset])

    def _parse_chunk_result(self, chunk: Any) -> ChunkResult:
        """Parse a Cognee chunk result into structured data."""
        # Handle different result types from Cognee
        text = ""
        chunk_id = ""
        created_at = ""

        if hasattr(chunk, "text"):
            text = chunk.text
        elif hasattr(chunk, "content"):
            text = chunk.content
        elif isinstance(chunk, dict):
            text = chunk.get("text", chunk.get("content", str(chunk)))
            chunk_id = chunk.get("id", "")
            created_at = chunk.get("created_at", "")
        else:
            text = str(chunk)

        if not isinstance(chunk, dict) and hasattr(chunk, "id"):
            chunk_id = str(chunk.id)
        if not isinstance(chunk, dict) and hasattr(chunk, "created_at"):
            # Handle Unix timestamp (ms)
            ts = chunk.created_at
            if isinstance(ts, (int, float)):
                created_at = datetime.fromtimestamp(ts / 1000).isoformat()
            else:
                created_at = str(ts)

        # Parse metadata from content prefix: [source: ui | tags: tag1,tag2 | created_at: ...]
        source = "manual"
        tags: list[str] = []
        content = text

        meta_match = re.match(r"^\[([^\]]+)\]\n?", text)
        if meta_match:
            meta_str = meta_match.group(1)
            content = text[meta_match.end():]

            # Parse source
            source_match = re.search(r"source:\s*(\w+)", meta_str)
            if source_match:
                source = source_match.group(1)

            # Parse tags
            tags_match = re.search(r"tags:\s*([^|]*)", meta_str)
            if tags_match:
                tags_str = tags_match.group(1).strip()
                if tags_str:
                    tags = [t.strip() for t in tags_str.split(",") if t.strip()]

            # Parse created_at from metadata if not from chunk
            if not created_at:
                created_match = re.search(r"created_at:\s*([^\s|]+)", meta_str)
                if created_match:
                    created_at = created_match.group(1)

        # Normalize created_at: int/float timestamps (ms) → ISO string
        if isinstance(created_at, (int, float)):
            created_at = datetime.fromtimestamp(created_at / 1000).isoformat()
        elif created_at:
            created_at = str(created_at)

        return ChunkResult(
            id=chunk_id or str(uuid.uuid4()),
            content=content.strip(),
            source=source,
            tags=tags,
            created_at=created_at or datetime.now().isoformat(),
        )

    async def search(
        self,
        query: str,
        dataset_name: str | None = None,
        search_type: str = "graph_completion"
    ) -> list[ChunkResult]:
        """
        Search the knowledge graph.

        search_type: "graph_completion" | "chunks"
        """
        dataset = dataset_name or self.DEFAULT_DATASET

        if search_type == "chunks":
            results = await cognee.search(
                query_type=SearchType.CHUNKS,
                query_text=query,
                datasets=[dataset]
            )
        else:
            results = await cognee.search(
                query_type=SearchType.GRAPH_COMPLETION,
                query_text=query
            )

        return [self._parse_chunk_result(r) for r in results]

    async def update_note(
        self,
        note_id: str,
        content: str,
        metadata: dict | None = None,
        dataset_name: str | None = None,
    ) -> bool:
        """
        Update a note by removing old chunks and re-adding with new content.

        Cognee doesn't support in-place updates, so we delete and re-add.
        """
        dataset = dataset_name or self.DEFAULT_DATASET

        # Remove old chunks for this note from Neo4j
        from app.config import get_settings
        from neo4j import AsyncGraphDatabase

        settings = get_settings()
        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        async with driver.session() as session:
            await session.run(
                "MATCH (n:DocumentChunk) "
                "WHERE n.id = $note_id OR elementId(n) = $note_id "
                "DETACH DELETE n",
                note_id=note_id,
            )
        await driver.close()

        await cognee.add([self._enrich_content(content, metadata)], dataset_name=dataset)

        return True

    async def delete_note(
        self,
        note_id: str,
    ) -> bool:
        """Delete a note and its chunks from Neo4j."""
        from app.config import get_settings
        from neo4j import AsyncGraphDatabase

        settings = get_settings()
        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        async with driver.session() as session:
            await session.run(
                "MATCH (n:DocumentChunk) "
                "WHERE n.id = $note_id OR elementId(n) = $note_id "
                "DETACH DELETE n",
                note_id=note_id,
            )
        await driver.close()

        return True

    async def get_notes_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
        dataset_name: str | None = None
    ) -> list[ChunkResult]:
        """
        Get notes created within a date range.
        Used for digest generation.
        """
        # For MVP, we'll search by date terms
        # In production, store metadata in a separate DB
        query = f"notes from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        return await self.search(query, dataset_name)
