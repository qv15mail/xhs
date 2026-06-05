from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class CollectTask(SQLModel, table=True):
    __tablename__ = "collect_task"

    id: str = Field(primary_key=True)
    topic: str
    total: int = 30
    progress: int = 0
    status: str = "pending"  # pending/running/success/failed
    sort: str = "comprehensive"
    include_comments: bool = False
    error: str | None = None
    created_at: datetime = Field(default_factory=_now)


class Note(SQLModel, table=True):
    __tablename__ = "note"

    id: str = Field(primary_key=True)
    task_id: str = Field(index=True)
    note_id: str = ""
    title: str = ""
    content: str = ""
    author: str = ""
    likes: int = 0
    collects: int = 0
    comments: int = 0
    shares: int = 0
    publish_time: str = ""
    url: str = ""
    cover: str = ""
    images_json: str = "[]"
    tags_json: str = "[]"
    created_at: datetime = Field(default_factory=_now)


class ComposeResult(SQLModel, table=True):
    __tablename__ = "compose_result"

    id: str = Field(primary_key=True)
    ref_note_id: str | None = None
    topic: str = ""
    titles_json: str = "[]"
    body: str = ""
    hashtags_json: str = "[]"
    images_json: str = "[]"
    created_at: datetime = Field(default_factory=_now)


class Setting(SQLModel, table=True):
    __tablename__ = "setting"

    key: str = Field(primary_key=True)
    value_json: str = "{}"
