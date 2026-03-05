from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.services.stats_service import StatsService

router = APIRouter()


def get_stats_service() -> StatsService:
    """Dependency for StatsService."""
    return StatsService()


class StatsResponse(BaseModel):
    notes: int
    topics: int
    connections: int
    this_week: int


class GraphNode(BaseModel):
    id: str
    label: str
    content: str


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ActivityItem(BaseModel):
    type: Literal["note", "search", "digest"]
    label: str
    timestamp: str
    preview: str | None = None


class ActivityResponse(BaseModel):
    items: list[ActivityItem]


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    stats_service: StatsService = Depends(get_stats_service),
):
    """Return dashboard KPI statistics."""
    try:
        return await stats_service.get_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}",
        )


@router.get("/graph", response_model=GraphResponse)
async def get_graph(
    stats_service: StatsService = Depends(get_stats_service),
):
    """Return nodes and edges for knowledge graph visualization."""
    try:
        return await stats_service.get_graph()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch graph: {str(e)}",
        )


@router.get("/activity", response_model=ActivityResponse)
async def get_activity(
    limit: int = Query(default=20, ge=1, le=100),
    stats_service: StatsService = Depends(get_stats_service),
):
    """Return recent activity timeline for the dashboard."""
    try:
        items = await stats_service.get_activity(limit=limit)
        return ActivityResponse(items=[ActivityItem(**item) for item in items])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch activity: {str(e)}",
        )
