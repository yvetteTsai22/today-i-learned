from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
import uuid

from app.models.digest import DigestResponse, TopicSuggestion
from app.models.content import ContentFormat, ContentGenerationRequest, ContentGenerationResponse
from app.services.cognee_service import CogneeService
from app.services.llm_service import LLMService

router = APIRouter()


def get_cognee_service() -> CogneeService:
    """Dependency for CogneeService."""
    return CogneeService()


def get_llm_service() -> LLMService:
    """Dependency for LLMService."""
    return LLMService()


@router.post("/digest", response_model=DigestResponse, status_code=status.HTTP_201_CREATED)
async def create_digest(
    cognee_service: CogneeService = Depends(get_cognee_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Generate a weekly digest from recent knowledge.
    """
    try:
        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        date_range = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

        # Get recent chunks from Cognee
        chunks = await cognee_service.search(
            query="recent learnings and insights",
            search_type="chunks"
        )

        if not chunks:
            # If no chunks, return empty digest
            return DigestResponse(
                id=str(uuid.uuid4()),
                summary="No new knowledge added this week.",
                suggested_topics=[],
                week_start=start_date,
                week_end=end_date,
                created_at=datetime.now(),
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

        return DigestResponse(
            id=str(uuid.uuid4()),
            summary=digest_data.get("summary", ""),
            suggested_topics=topics,
            week_start=start_date,
            week_end=end_date,
            created_at=datetime.now(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create digest: {str(e)}"
        )


@router.post("/digest/content", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Generate content drafts for a topic in specified formats.
    """
    try:
        result = ContentGenerationResponse(topic=request.topic)

        for fmt in request.formats:
            if fmt == ContentFormat.BLOG:
                result.blog = await llm_service.generate_blog_draft(
                    topic=request.topic,
                    source_chunks=request.source_chunks
                )
            elif fmt == ContentFormat.LINKEDIN:
                result.linkedin = await llm_service.generate_linkedin_post(
                    topic=request.topic,
                    source_chunks=request.source_chunks
                )
            elif fmt == ContentFormat.X_THREAD:
                result.x_thread = await llm_service.generate_x_thread(
                    topic=request.topic,
                    source_chunks=request.source_chunks
                )
            elif fmt == ContentFormat.VIDEO_SCRIPT:
                result.video_script = await llm_service.generate_video_script(
                    topic=request.topic,
                    source_chunks=request.source_chunks
                )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )
