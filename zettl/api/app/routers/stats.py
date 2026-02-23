from fastapi import APIRouter, Depends, HTTPException, status
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
