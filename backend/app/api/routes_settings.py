from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.db import get_session
from app.schemas import SettingsOut, TestLLMOut
from app.services.llm import LLMClient
from app.services.settings_store import get_llm_settings, get_settings, save_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def read_settings(session: Session = Depends(get_session)):
    return get_settings(session)


@router.put("", response_model=SettingsOut)
def update_settings(data: SettingsOut, session: Session = Depends(get_session)):
    return save_settings(session, data)


@router.post("/test-llm", response_model=TestLLMOut)
async def test_llm(session: Session = Depends(get_session)):
    llm = LLMClient(get_llm_settings(session))
    ok, message = await llm.test()
    return TestLLMOut(ok=ok, message=message)
