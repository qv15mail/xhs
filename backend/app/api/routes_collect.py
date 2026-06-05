import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sse_starlette.sse import EventSourceResponse

from app.api.mappers import task_to_out
from app.core.db import get_session
from app.models import CollectTask
from app.schemas import CreateTaskRequest, TaskOut
from app.services.collector import new_task_id
from app.services.tasks import task_manager

router = APIRouter(prefix="/api/collect", tags=["collect"])


@router.post("/tasks", response_model=TaskOut)
async def create_task(req: CreateTaskRequest, session: Session = Depends(get_session)):
    task = CollectTask(
        id=new_task_id(),
        topic=req.topic,
        total=req.total,
        sort=req.sort,
        include_comments=req.includeComments,
        status="pending",
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    task_manager.start(task.id)
    return task_to_out(task)


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(session: Session = Depends(get_session)):
    rows = session.exec(select(CollectTask).order_by(CollectTask.created_at.desc())).all()
    return [task_to_out(t) for t in rows]


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: str, session: Session = Depends(get_session)):
    task = session.get(CollectTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task_to_out(task)


@router.get("/tasks/{task_id}/events")
async def task_events(task_id: str, session: Session = Depends(get_session)):
    if not session.get(CollectTask, task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    queue = task_manager.subscribe(task_id)

    async def gen():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": "{}"}
                    continue
                yield {"event": event.get("type", "message"), "data": json.dumps(event)}
                if event.get("type") in ("done", "error"):
                    break
        finally:
            task_manager.unsubscribe(task_id, queue)

    return EventSourceResponse(gen())
