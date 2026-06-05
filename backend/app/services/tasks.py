import asyncio
from collections import defaultdict

from sqlmodel import Session

from app.core.db import engine
from app.models import CollectTask, Note
from app.services.collector import Collector, RateLimiter


class TaskManager:
    """采集任务编排：asyncio 执行 + 进度落库 + SSE 事件广播。"""

    def __init__(self):
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._running: set[str] = set()

    def subscribe(self, task_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues[task_id].append(q)
        return q

    def unsubscribe(self, task_id: str, q: asyncio.Queue) -> None:
        if q in self._queues.get(task_id, []):
            self._queues[task_id].remove(q)

    async def _emit(self, task_id: str, event: dict) -> None:
        for q in list(self._queues.get(task_id, [])):
            await q.put(event)

    def start(self, task_id: str) -> None:
        if task_id in self._running:
            return
        self._running.add(task_id)
        asyncio.create_task(self.run_task(task_id))

    async def run_task(self, task_id: str) -> None:
        try:
            with Session(engine) as session:
                task = session.get(CollectTask, task_id)
                if not task:
                    return
                task.status = "running"
                session.add(task)
                session.commit()
                topic, total = task.topic, task.total
                from app.services.settings_store import get_settings

                cfg = get_settings(session).collect
                level, concurrency = cfg.rateLevel, cfg.concurrency

            limiter = RateLimiter(level=level, concurrency=concurrency)
            collector = Collector()
            collected = 0

            async def on_note(note: Note) -> None:
                nonlocal collected
                with Session(engine) as s:
                    s.add(note)
                    t = s.get(CollectTask, task_id)
                    if t:
                        collected += 1
                        t.progress = collected
                        s.add(t)
                    s.commit()
                await self._emit(
                    task_id, {"type": "progress", "progress": collected, "total": total}
                )

            await collector.collect(task_id, topic, total, limiter, on_note)

            with Session(engine) as session:
                task = session.get(CollectTask, task_id)
                if task:
                    task.status = "success"
                    task.progress = collected
                    session.add(task)
                    session.commit()
            await self._emit(task_id, {"type": "done", "progress": collected, "total": total})
        except Exception as exc:  # noqa: BLE001
            with Session(engine) as session:
                task = session.get(CollectTask, task_id)
                if task:
                    task.status = "failed"
                    task.error = str(exc)
                    session.add(task)
                    session.commit()
            await self._emit(task_id, {"type": "error", "message": str(exc)})
        finally:
            self._running.discard(task_id)


task_manager = TaskManager()
