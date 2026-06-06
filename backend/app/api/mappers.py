import json

from app.models import CollectTask, Note
from app.schemas import NoteOut, TaskOut


def task_to_out(t: CollectTask) -> TaskOut:
    return TaskOut(
        id=t.id,
        topic=t.topic,
        total=t.total,
        progress=t.progress,
        status=t.status,
        sort=t.sort,
        includeComments=t.include_comments,
        error=t.error,
        createdAt=t.created_at.isoformat(),
    )


def note_to_out(n: Note) -> NoteOut:
    return NoteOut(
        id=n.id,
        taskId=n.task_id,
        title=n.title,
        content=n.content,
        author=n.author,
        likes=n.likes,
        collects=n.collects,
        comments=n.comments,
        shares=n.shares,
        publishTime=n.publish_time,
        url=n.url,
        cover=n.cover,
        tags=json.loads(n.tags_json or "[]"),
        createdAt=n.created_at.isoformat(),
    )
