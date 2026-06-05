from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.db import get_session
from app.models import Note
from app.schemas import BreakdownOut, BreakdownRequest, KeywordOut, RankingOut
from app.services.analysis import build_ranking, extract_keywords, llm_breakdown
from app.services.llm import LLMClient
from app.services.settings_store import get_llm_settings

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def _notes_for_task(session: Session, task_id: str | None) -> list[Note]:
    stmt = select(Note)
    if task_id and task_id != "all":
        stmt = stmt.where(Note.task_id == task_id)
    return list(session.exec(stmt).all())


@router.get("/{task_id}")
def analysis(task_id: str, session: Session = Depends(get_session)):
    notes = _notes_for_task(session, task_id)
    keywords: list[KeywordOut] = extract_keywords(notes)
    ranking: list[RankingOut] = build_ranking(notes)
    return {"keywords": keywords, "ranking": ranking}


@router.post("/breakdown", response_model=BreakdownOut)
async def breakdown(req: BreakdownRequest, session: Session = Depends(get_session)):
    note = session.get(Note, req.noteId)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    llm = LLMClient(get_llm_settings(session))
    return await llm_breakdown(note, llm)
