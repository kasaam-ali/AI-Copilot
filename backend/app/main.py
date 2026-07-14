"""FastAPI application entrypoint."""

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import explain, health, inspect
from app.config import get_settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    settings = get_settings()
    settings.artifact_path.mkdir(parents=True, exist_ok=True)
    init_db()
    logger.info("{} backend started", settings.app_name)
    yield
    logger.info("{} backend stopped", settings.app_name)


app = FastAPI(title="SentinelQ API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Attach a unique request id to every response for traceability."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(health.router, prefix="/api/v1")
app.include_router(inspect.router, prefix="/api/v1")
app.include_router(explain.router, prefix="/api/v1")
