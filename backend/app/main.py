"""FastAPI application factory for CyberScore."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialize DB on startup."""
    await init_db()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance.
    """
    app = FastAPI(
        title="CyberScore API",
        description="Sovereign Cyber Scoring & VRM Platform",
        version="1.0.0",
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import router here to avoid circular imports
    from app.api.v1 import router as api_v1_router

    app.include_router(api_v1_router, prefix="/api/v1")

    @app.get("/health")
    async def root_health() -> dict:
        """Root health check endpoint."""
        return {"status": "ok", "service": "cyberscore-api"}

    return app


app = create_app()
