import cognee
from cognee.modules.search.types import SearchType
from datetime import datetime
import uuid


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

    async def search(
        self,
        query: str,
        dataset_name: str | None = None,
        search_type: str = "graph_completion"
    ) -> list[str]:
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

        return [str(r) for r in results]

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
