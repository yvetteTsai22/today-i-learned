import pytest
from datetime import datetime
from app.models.note import NoteCreate, NoteResponse, NoteSource


def test_note_create_with_defaults():
    note = NoteCreate(content="Test content")
    assert note.content == "Test content"
    assert note.source == NoteSource.MANUAL
    assert note.tags == []


def test_note_create_with_all_fields():
    note = NoteCreate(
        content="Test content",
        source=NoteSource.AGENT,
        tags=["test", "example"],
        source_reference="claude-code-session-123"
    )
    assert note.source == NoteSource.AGENT
    assert "test" in note.tags


def test_note_response_has_id_and_timestamps():
    response = NoteResponse(
        id="note-123",
        content="Test",
        source=NoteSource.MANUAL,
        tags=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert response.id == "note-123"
    assert response.created_at is not None
