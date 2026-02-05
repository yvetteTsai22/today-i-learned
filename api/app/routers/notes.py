from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.note import NoteCreate, NoteResponse, NoteSource
from app.services.cognee_service import CogneeService

router = APIRouter()


def get_cognee_service() -> CogneeService:
    """Dependency for CogneeService - enables easy mocking in tests."""
    return CogneeService()


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    search_type: str = Field(default="graph_completion")


class SearchResponse(BaseModel):
    results: list[str]
    query: str


@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note: NoteCreate,
    cognee_service: CogneeService = Depends(get_cognee_service)
):
    """
    Create a new note and process it into the knowledge graph.
    """
    try:
        metadata = {
            "source": note.source.value,
            "tags": ",".join(note.tags) if note.tags else "",
            "created_at": datetime.now().isoformat(),
        }
        if note.source_reference:
            metadata["source_reference"] = note.source_reference

        note_id = await cognee_service.add_note(
            content=note.content,
            metadata=metadata
        )

        now = datetime.now()
        return NoteResponse(
            id=note_id,
            content=note.content,
            source=note.source,
            tags=note.tags,
            created_at=now,
            updated_at=now,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create note: {str(e)}"
        )


@router.post("/search", response_model=SearchResponse)
async def search_notes(
    request: SearchRequest,
    cognee_service: CogneeService = Depends(get_cognee_service)
):
    """
    Search the knowledge graph.
    """
    try:
        results = await cognee_service.search(
            query=request.query,
            search_type=request.search_type
        )
        return SearchResponse(results=results, query=request.query)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
