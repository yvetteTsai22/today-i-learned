from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class NoteSource(str, Enum):
    MANUAL = "manual"
    NOTION = "notion"
    AGENT = "agent"
    UI = "ui"


class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Note content")
    source: NoteSource = Field(default=NoteSource.MANUAL, description="Origin of the note")
    tags: list[str] = Field(default_factory=list, description="Optional tags")
    source_reference: str | None = Field(default=None, description="External reference ID")


class NoteResponse(BaseModel):
    id: str
    content: str
    source: NoteSource
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
