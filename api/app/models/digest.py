from datetime import datetime
from pydantic import BaseModel, Field


class TopicSuggestion(BaseModel):
    title: str
    reasoning: str
    relevant_chunks: list[str] = Field(default_factory=list)


class DigestResponse(BaseModel):
    id: str
    summary: str
    suggested_topics: list[TopicSuggestion]
    week_start: datetime
    week_end: datetime
    created_at: datetime
