import json
import uuid

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.db import get_session
from app.models import ComposeResult, Note
from app.schemas import ComposeOut, ComposeRequest
from app.services.compose import compose_note
from app.services.llm import LLMClient
from app.services.settings_store import get_llm_settings

router = APIRouter(prefix="/api/compose", tags=["compose"])


@router.post("", response_model=ComposeOut)
async def compose(req: ComposeRequest, session: Session = Depends(get_session)):
    ref: Note | None = session.get(Note, req.refNoteId) if req.refNoteId else None
    llm = LLMClient(get_llm_settings(session))
    result = await compose_note(req, ref, llm)

    session.add(
        ComposeResult(
            id=f"cmp-{uuid.uuid4().hex[:10]}",
            ref_note_id=req.refNoteId,
            topic=req.topic,
            titles_json=json.dumps(result.titles, ensure_ascii=False),
            body=result.body,
            hashtags_json=json.dumps(result.hashtags, ensure_ascii=False),
            images_json=json.dumps(result.imageSuggestions, ensure_ascii=False),
        )
    )
    session.commit()
    return result
