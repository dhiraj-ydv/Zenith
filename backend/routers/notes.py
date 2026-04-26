"""
Notes Router — CRUD endpoints for markdown notes.
"""

from fastapi import APIRouter, HTTPException, Query

from models import NoteCreate, NoteUpdate, NoteRename, NoteResponse, NoteSummary
from services.notes import NoteService

router = APIRouter(prefix="/api/notes", tags=["Notes"])

# Injected at startup
note_service: NoteService = None  # type: ignore


@router.get("", response_model=list[NoteSummary])
async def list_notes(label: str | None = Query(None, description="Filter by label")):
    """List all notes, optionally filtered by a label."""
    return note_service.list_notes(label=label)


@router.get("/search", response_model=list[NoteSummary])
async def search_notes(q: str = Query(..., min_length=1)):
    """Search note titles for autocomplete."""
    return note_service.search_titles(q)


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str):
    """Get a single note by ID."""
    note = note_service.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.get("/{note_id}/raw")
async def get_note_raw(note_id: str):
    """Get raw markdown text of a note (LLM-friendly)."""
    raw = note_service.get_raw(note_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"id": note_id, "content": raw}


@router.post("", response_model=NoteResponse, status_code=201)
async def create_note(body: NoteCreate):
    """Create a new note."""
    try:
        return note_service.create_note(body.title, body.content, body.labels)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: str, body: NoteUpdate):
    """Update a note's content and/or labels."""
    note = note_service.update_note(note_id, body.content, body.labels)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.patch("/{note_id}/rename", response_model=NoteResponse)
async def rename_note(note_id: str, body: NoteRename):
    """Rename a note."""
    try:
        note = note_service.rename_note(note_id, body.new_title)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: str):
    """Delete a note and garbage-collect orphaned attachments."""
    if not note_service.delete_note(note_id):
        raise HTTPException(status_code=404, detail="Note not found")
