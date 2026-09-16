"""
CITY TYCOON Mini App backend.

Run with:  uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import router as api_router
from bot.config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("city_tycoon.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting CITY TYCOON backend | environment=%s | webapp_configured=%s",
        settings.ENVIRONMENT,
        settings.webapp_configured,
    )
    yield
    logger.info("Shutting down CITY TYCOON backend")


app = FastAPI(title="CITY TYCOON API", lifespan=lifespan)

# In production WEBAPP_URL is the Mini App's own deployed origin — that's
# the only origin that legitimately needs to call this API. Falls back to
# "*" only for local development when WEBAPP_URL isn't set yet.
_allowed_origins = [settings.WEBAPP_URL] if settings.webapp_configured else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "PATCH"],
    allow_headers=["Authorization", "X-Telegram-Init-Data", "Content-Type"],
)

app.include_router(api_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}