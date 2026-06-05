from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from app.core.db import get_session
from app.models import CollectTask, Note

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
def stats(session: Session = Depends(get_session)):
    total_notes = session.exec(select(func.count()).select_from(Note)).one()
    total_tasks = session.exec(select(func.count()).select_from(CollectTask)).one()
    avg_engagement_row = session.exec(
        select(func.avg(Note.likes + Note.collects)).select_from(Note)
    ).one()
    avg_engagement = int(avg_engagement_row or 0)

    last_task = session.exec(
        select(CollectTask).order_by(CollectTask.created_at.desc()).limit(1)
    ).first()

    now = datetime.now(timezone.utc)
    trend = []
    for i in range(6, -1, -1):
        day = now - timedelta(days=i)
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        count = session.exec(
            select(func.count())
            .select_from(Note)
            .where(Note.created_at >= start, Note.created_at < end)
        ).one()
        trend.append({"date": start.isoformat(), "count": count})

    return {
        "totalNotes": total_notes,
        "totalTasks": total_tasks,
        "avgEngagement": avg_engagement,
        "lastTaskStatus": last_task.status if last_task else "none",
        "trend": trend,
    }
