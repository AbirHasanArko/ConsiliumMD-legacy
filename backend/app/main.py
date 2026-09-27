"""ConsiliumMD FastAPI app factory."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.cases import router as cases_router, _decision_classes_router
from app.api.patients import router as patients_router
from app.api.recommendations import router as recommendations_router
from app.api.review import router as review_router
from app.api.users import router as users_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ConsiliumMD",
        description=(
            "Multi-role clinical decision support built around the CARMA "
            "reasoning engine. This MVP ships with a mock reasoning provider; "
            "Phase 2 swaps in CARMA's HTTP API without UI changes."
        ),
        version=__version__,
        lifespan=lifespan,
    )

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/v1/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok", "version": __version__, "service": "consilium"}

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(patients_router, prefix="/api/v1")
    app.include_router(cases_router, prefix="/api/v1")
    app.include_router(_decision_classes_router, prefix="/api/v1")
    app.include_router(recommendations_router, prefix="/api/v1")
    app.include_router(review_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")
    return app


app = create_app()
