"""API v1 router — aggregates all sub-routers."""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.health import router as health_router
from app.api.v1.reports import router as reports_router
from app.api.v1.scoring import router as scoring_router
from app.api.v1.vendors import router as vendors_router

router = APIRouter()

router.include_router(health_router)
router.include_router(vendors_router)
router.include_router(scoring_router)
router.include_router(alerts_router)
router.include_router(reports_router)
router.include_router(admin_router)
