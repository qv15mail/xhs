from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.mappers import note_to_out
from app.core.db import get_session
from app.models import Note
from app.schemas import NoteOut

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.get("", response_model=list[NoteOut])
def list_notes(
    taskId: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    stmt = select(Note)
    if taskId:
        stmt = stmt.where(Note.task_id == taskId)
    stmt = stmt.order_by(Note.created_at.desc()).limit(limit)
    return [note_to_out(n) for n in session.exec(stmt).all()]


@router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: str, session: Session = Depends(get_session)):
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return note_to_out(note)
