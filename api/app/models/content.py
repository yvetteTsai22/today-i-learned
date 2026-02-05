from pydantic import BaseModel, Field
from enum import Enum


class ContentFormat(str, Enum):
    BLOG = "blog"
    LINKEDIN = "linkedin"
    X_THREAD = "x_thread"
    VIDEO_SCRIPT = "video_script"


class ContentGenerationRequest(BaseModel):
    topic: str
    source_chunks: list[str]
    formats: list[ContentFormat] = Field(
        default=[ContentFormat.BLOG, ContentFormat.LINKEDIN, ContentFormat.X_THREAD, ContentFormat.VIDEO_SCRIPT]
    )


class ContentGenerationResponse(BaseModel):
    topic: str
    blog: str | None = None
    linkedin: str | None = None
    x_thread: str | None = None
    video_script: str | None = None
