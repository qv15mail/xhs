import json

from sqlmodel import Session

from app.core.config import settings as env_settings
from app.models import Setting
from app.schemas import CollectSettings, LLMSettings, SettingsOut

_LLM_KEY = "llm"
_COLLECT_KEY = "collect"


def _default_llm() -> LLMSettings:
    return LLMSettings(
        baseUrl=env_settings.llm_base_url,
        apiKey=env_settings.llm_api_key,
        model=env_settings.llm_model,
        temperature=env_settings.llm_temperature,
    )


def get_settings(session: Session) -> SettingsOut:
    llm_row = session.get(Setting, _LLM_KEY)
    collect_row = session.get(Setting, _COLLECT_KEY)
    llm = LLMSettings(**json.loads(llm_row.value_json)) if llm_row else _default_llm()
    collect = (
        CollectSettings(**json.loads(collect_row.value_json))
        if collect_row
        else CollectSettings()
    )
    return SettingsOut(llm=llm, collect=collect)


def save_settings(session: Session, data: SettingsOut) -> SettingsOut:
    for key, value in ((_LLM_KEY, data.llm), (_COLLECT_KEY, data.collect)):
        row = session.get(Setting, key)
        payload = json.dumps(value.model_dump(), ensure_ascii=False)
        if row:
            row.value_json = payload
        else:
            row = Setting(key=key, value_json=payload)
        session.add(row)
    session.commit()
    return get_settings(session)


def get_llm_settings(session: Session) -> LLMSettings:
    return get_settings(session).llm
