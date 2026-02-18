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


class CogneeService:
    """Service for interacting with Cognee knowledge graph."""

    DEFAULT_DATASET = "zettl_notes"

    async def add_note(
        self,
        content: str,
        dataset_name: str | None = None,
        metadata: dict | None = None
    ) -> str:
        """
        Add a note to Cognee and process it into the knowledge graph.

        Returns the note ID.
        """
        dataset = dataset_name or self.DEFAULT_DATASET
        note_id = str(uuid.uuid4())

        # Prepare content with metadata
        enriched_content = content
        if metadata:
            meta_str = " | ".join(f"{k}: {v}" for k, v in metadata.items())
            enriched_content = f"[{meta_str}]\n{content}"

        # Add to Cognee
        await cognee.add([enriched_content], dataset_name=dataset)

        # Process into knowledge graph
        await cognee.cognify([dataset])

        return note_id

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

        if hasattr(chunk, "id"):
            chunk_id = str(chunk.id)
        if hasattr(chunk, "created_at"):
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

    async def get_notes_in_range(
        self,
        start_date: datetime,
        end_date: datetime,
        dataset_name: str | None = None
    ) -> list[str]:
        """
        Get notes created within a date range.
        Used for digest generation.
        """
        # For MVP, we'll search by date terms
        # In production, store metadata in a separate DB
        query = f"notes from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        return await self.search(query, dataset_name)
