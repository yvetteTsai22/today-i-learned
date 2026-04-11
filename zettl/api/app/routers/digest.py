import functools
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

from app.models.digest import DigestResponse, TopicSuggestion
from app.models.content import ContentFormat, ContentGenerationRequest, ContentGenerationResponse
from app.services.cognee_service import CogneeService, is_cognee_no_data_error
from app.services.llm_service import LLMService
from app.services.digest_cache_service import DigestCacheService
from app.services.content_agent import ContentAgentService

router = APIRouter()


def get_cognee_service() -> CogneeService:
    """Dependency for CogneeService."""
    return CogneeService()


def get_llm_service() -> LLMService:
    """Dependency for LLMService."""
    return LLMService()


def get_digest_cache_service() -> DigestCacheService:
    """Dependency for DigestCacheService."""
    return DigestCacheService()


@functools.lru_cache(maxsize=1)
def get_content_agent_service() -> ContentAgentService:
    """Dependency for ContentAgentService. Cached so the LangGraph is only compiled once."""
    return ContentAgentService()


@router.post("/digest", response_model=DigestResponse, status_code=status.HTTP_201_CREATED)
async def create_digest(
    force_refresh: bool = False,
    cognee_service: CogneeService = Depends(get_cognee_service),
    llm_service: LLMService = Depends(get_llm_service),
    cache_service: DigestCacheService = Depends(get_digest_cache_service),
):
    """
    Generate a weekly digest from recent knowledge.
    Returns cached result if available for the current calendar week.
    """
    try:
        now = datetime.now()
        year, week, _ = now.isocalendar()

        # Check cache (unless force refresh requested)
        if not force_refresh:
            cached = await cache_service.get_cached_digest(year, week)
            if cached is not None:
                return cached

        # Calculate date range (last 7 days)
        end_date = now
        start_date = end_date - timedelta(days=7)
        date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

        # Get recent chunks from Cognee
        try:
            chunks = await cognee_service.search(
                query="recent learnings and insights",
                search_type="chunks"
            )
        except Exception as e:
            if is_cognee_no_data_error(e):
                chunks = []
            else:
                raise

        if not chunks:
            return DigestResponse(
                id=str(uuid.uuid4()),
                summary="No new knowledge added this week.",
                suggested_topics=[],
                week_start=start_date,
                week_end=end_date,
                created_at=now,
            )

        # Generate digest summary with LLM
        digest_data = await llm_service.generate_digest_summary(
            chunks=chunks,
            date_range=date_range
        )

        # Parse topics
        topics = [
            TopicSuggestion(
                title=t.get("title", ""),
                reasoning=t.get("reasoning", ""),
                relevant_chunks=t.get("relevant_chunks", [])
            )
            for t in digest_data.get("topics", [])
        ]

        response = DigestResponse(
            id=str(uuid.uuid4()),
            summary=digest_data.get("summary", ""),
            suggested_topics=topics,
            week_start=start_date,
            week_end=end_date,
            created_at=now,
        )

        # Store in cache
        await cache_service.store_digest(year, week, response)

        return response

    except Exception as e:
        logger.exception("Failed to create digest")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create digest: {str(e)}"
        )


@router.post("/digest/content", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    agent: ContentAgentService = Depends(get_content_agent_service),
):
    """
    Generate content drafts for a topic in specified formats.
    Uses a LangGraph agent with SKILL.md-based content skills.
    """
    try:
        return await agent.generate(
            topic=request.topic,
            source_chunks=request.source_chunks,
            formats=request.formats,
        )
    except Exception as e:
        logger.exception("Failed to generate content for topic=%s", request.topic)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )
