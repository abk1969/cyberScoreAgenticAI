"""Health check endpoint with DB and Redis connectivity status."""

from fastapi import APIRouter
from sqlalchemy import text

from app.database import async_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Return the health status of the API and its dependencies."""
    status_report: dict = {
        "status": "ok",
        "service": "mh-cyberscore-api",
        "dependencies": {},
    }

    # Check database
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        status_report["dependencies"]["database"] = "ok"
    except Exception as exc:
        status_report["dependencies"]["database"] = f"error: {exc}"
        status_report["status"] = "degraded"

    # Check Redis
    try:
        import redis.asyncio as aioredis

        from app.config import settings

        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        status_report["dependencies"]["redis"] = "ok"
    except Exception as exc:
        status_report["dependencies"]["redis"] = f"error: {exc}"
        status_report["status"] = "degraded"

    return status_report
