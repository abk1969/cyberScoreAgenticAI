"""Internal scoring endpoints: AD Rating, M365 Rating, GRC/PSSI."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.internal_scoring import InternalFinding, InternalScan
from app.schemas.grc import FrameworkCoverage, HeatmapCell, MaturityData, SecurityControlResponse, SecurityControlUpdate
from app.schemas.internal import InternalFindingResponse, InternalScanCreate, InternalScanResponse
from app.services.ad_rating_service import ADRatingService
from app.services.grc_service import GRCService
from app.services.m365_rating_service import M365RatingService

router = APIRouter(prefix="/internal", tags=["internal"])


# ── AD Rating ───────────────────────────────────────────────────────────


@router.post("/ad/scan", response_model=InternalScanResponse, status_code=status.HTTP_201_CREATED)
async def scan_ad(
    config: InternalScanCreate,
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(require_role("admin", "rssi")),
) -> InternalScanResponse:
    """Trigger an Active Directory security scan."""
    service = ADRatingService(db)
    scan = await service.scan_domain(
        domain_controller=config.target,
        credentials=config.config.get("credentials"),
        threshold_dormant_days=config.config.get("threshold_dormant_days", 90),
    )
    return InternalScanResponse.model_validate(scan)


@router.get("/ad/score")
async def get_ad_score(
    target: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> dict:
    """Get the latest AD security score."""
    service = ADRatingService(db)
    score = await service.get_score(target)
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No AD scan found",
        )
    return score


@router.get("/ad/history")
async def get_ad_history(
    target: str | None = Query(None),
    limit: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> list[dict]:
    """Get AD scan score history."""
    service = ADRatingService(db)
    return await service.get_history(target, limit)


@router.get("/ad/findings", response_model=list[InternalFindingResponse])
async def get_ad_findings(
    severity: str | None = Query(None, pattern=r"^(critical|high|medium|low|info)$"),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> list[InternalFindingResponse]:
    """Get findings from the latest AD scan."""
    # Get latest AD scan
    scan_result = await db.execute(
        select(InternalScan)
        .where(InternalScan.scan_type == "ad")
        .order_by(InternalScan.created_at.desc())
        .limit(1)
    )
    scan = scan_result.scalar_one_or_none()
    if not scan:
        return []

    query = select(InternalFinding).where(InternalFinding.scan_id == scan.id)
    if severity:
        query = query.where(InternalFinding.severity == severity)
    if category:
        query = query.where(InternalFinding.category == category)
    query = query.order_by(InternalFinding.detected_at.desc())

    result = await db.execute(query)
    findings = result.scalars().all()
    return [InternalFindingResponse.model_validate(f) for f in findings]


# ── M365 Rating ─────────────────────────────────────────────────────────


@router.post("/m365/scan", response_model=InternalScanResponse, status_code=status.HTTP_201_CREATED)
async def scan_m365(
    config: InternalScanCreate,
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(require_role("admin", "rssi")),
) -> InternalScanResponse:
    """Trigger a Microsoft 365 security scan."""
    service = M365RatingService(db)
    scan = await service.scan_tenant(
        tenant_id=config.target,
        credentials=config.config.get("credentials"),
    )
    return InternalScanResponse.model_validate(scan)


@router.get("/m365/score")
async def get_m365_score(
    target: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> dict:
    """Get the latest M365 security score."""
    service = M365RatingService(db)
    score = await service.get_score(target)
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No M365 scan found",
        )
    return score


@router.get("/m365/findings", response_model=list[InternalFindingResponse])
async def get_m365_findings(
    severity: str | None = Query(None, pattern=r"^(critical|high|medium|low|info)$"),
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> list[InternalFindingResponse]:
    """Get findings from the latest M365 scan."""
    scan_result = await db.execute(
        select(InternalScan)
        .where(InternalScan.scan_type == "m365")
        .order_by(InternalScan.created_at.desc())
        .limit(1)
    )
    scan = scan_result.scalar_one_or_none()
    if not scan:
        return []

    query = select(InternalFinding).where(InternalFinding.scan_id == scan.id)
    if severity:
        query = query.where(InternalFinding.severity == severity)
    query = query.order_by(InternalFinding.detected_at.desc())

    result = await db.execute(query)
    findings = result.scalars().all()
    return [InternalFindingResponse.model_validate(f) for f in findings]


# ── GRC / PSSI ──────────────────────────────────────────────────────────


@router.get("/grc/controls")
async def get_grc_controls(
    domain: str | None = Query(None),
    control_status: str | None = Query(
        None,
        alias="status",
        pattern=r"^(implemented|partial|not_implemented)$",
    ),
    framework: str | None = Query(
        None,
        pattern=r"^(iso27001|dora|nis2|hds|rgpd)$",
    ),
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> list[dict]:
    """Get security controls with optional filters."""
    service = GRCService(db)
    return await service.get_controls(domain, control_status, framework)


@router.put("/grc/controls/{control_id}")
async def update_grc_control(
    control_id: str,
    update: SecurityControlUpdate,
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(require_role("admin", "rssi", "analyste_ssi")),
) -> dict:
    """Update a security control."""
    service = GRCService(db)
    result = await service.update_control(control_id, update.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Control {control_id} not found",
        )
    return result


@router.get("/grc/maturity")
async def get_grc_maturity(
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> dict:
    """Get overall GRC maturity score."""
    service = GRCService(db)
    return await service.get_maturity_score()


@router.get("/grc/coverage/{framework}")
async def get_framework_coverage(
    framework: str,
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> dict:
    """Get implementation coverage for a specific framework."""
    if framework not in ("iso27001", "dora", "nis2", "hds", "rgpd"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown framework: {framework}",
        )
    service = GRCService(db)
    return await service.get_coverage_by_framework(framework)


@router.get("/grc/heatmap")
async def get_grc_heatmap(
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> list[dict]:
    """Get GRC heatmap data (domain x framework matrix)."""
    service = GRCService(db)
    return await service.get_heatmap_data()
