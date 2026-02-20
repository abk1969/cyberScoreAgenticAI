"""API v1 router — aggregates all sub-routers."""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.benchmark import router as benchmark_router
from app.api.v1.compliance import router as compliance_router
from app.api.v1.health import router as health_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.internal import router as internal_router
from app.api.v1.portal import router as portal_router
from app.api.v1.questionnaires import router as questionnaires_router
from app.api.v1.reports import router as reports_router
from app.api.v1.scoring import router as scoring_router
from app.api.v1.bulk import router as bulk_router
from app.api.v1.chat import router as chat_router
from app.api.v1.supply_chain import router as supply_chain_router
from app.api.v1.vendors import router as vendors_router
from app.api.v1.vrm import router as vrm_router

router = APIRouter()

router.include_router(health_router)
router.include_router(vendors_router)
router.include_router(scoring_router)
router.include_router(alerts_router)
router.include_router(reports_router)
router.include_router(admin_router)
router.include_router(benchmark_router)
router.include_router(integrations_router)
router.include_router(portal_router)
router.include_router(compliance_router)
router.include_router(internal_router)
router.include_router(supply_chain_router)
router.include_router(chat_router)
router.include_router(bulk_router)
router.include_router(vrm_router)
router.include_router(questionnaires_router)
