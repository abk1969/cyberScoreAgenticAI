"""Supply Chain API — dependency graph and concentration risk endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.schemas.supply_chain import (
    AnalyzeRequest,
    ConcentrationRiskResponse,
    GraphData,
    VendorDependencyResponse,
)
from app.services.supply_chain_service import SupplyChainService

router = APIRouter(prefix="/supply-chain", tags=["supply-chain"])


@router.get("/graph", response_model=GraphData)
async def get_supply_chain_graph(
    vendor_ids: str | None = Query(
        None, description="Comma-separated vendor IDs to filter"
    ),
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> GraphData:
    """Return the full supply chain dependency graph (D3.js compatible)."""
    service = SupplyChainService(db)
    ids = vendor_ids.split(",") if vendor_ids else None
    return await service.build_dependency_graph(ids)


@router.get("/concentration", response_model=ConcentrationRiskResponse)
async def get_concentration_risk(
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> ConcentrationRiskResponse:
    """Calculate and return concentration risk analysis."""
    service = SupplyChainService(db)
    return await service.calculate_concentration_risk()


@router.get(
    "/vendors/{vendor_id}/dependencies",
    response_model=list[VendorDependencyResponse],
)
async def get_vendor_dependencies(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> list[VendorDependencyResponse]:
    """Get all Nth-party dependencies for a specific vendor."""
    service = SupplyChainService(db)
    return await service.get_vendor_dependencies(vendor_id)


@router.post("/analyze")
async def trigger_analysis(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> dict:
    """Trigger Nth-party analysis for the given vendors.

    Queues Celery tasks for each vendor and returns immediately.
    """
    from app.agents.nthparty_agent import detect_nthparty
    from app.models.vendor import Vendor

    from sqlalchemy import select

    vendor_q = select(Vendor).where(Vendor.id.in_(request.vendor_ids))
    result = await db.execute(vendor_q)
    vendors = result.scalars().all()

    queued = []
    for v in vendors:
        detect_nthparty.delay(v.id, v.domain)
        queued.append(v.id)

    return {
        "queued": len(queued),
        "vendor_ids": queued,
    }
