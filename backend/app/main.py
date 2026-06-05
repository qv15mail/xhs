from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    routes_analysis,
    routes_auth,
    routes_collect,
    routes_compose,
    routes_notes,
    routes_settings,
    routes_stats,
)
from app.core.config import settings
from app.core.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="RedScope API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_collect.router)
app.include_router(routes_notes.router)
app.include_router(routes_analysis.router)
app.include_router(routes_compose.router)
app.include_router(routes_settings.router)
app.include_router(routes_auth.router)
app.include_router(routes_stats.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "collectMode": settings.collect_mode}
