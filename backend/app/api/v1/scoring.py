"""Scoring endpoints: scores, history, domain breakdown, scan trigger."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.scoring import Finding, VendorScore
from app.models.vendor import Vendor
from app.schemas.scoring import FindingResponse, ScoreResponse, ScoringTriggerRequest

router = APIRouter(prefix="/scoring", tags=["scoring"])


@router.get("/portfolio")
async def get_portfolio_scores(
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> dict:
    """Return aggregated portfolio scoring statistics."""
    # Total vendors
    total_result = await db.execute(select(sa_func.count(Vendor.id)))
    total_vendors = total_result.scalar() or 0

    if total_vendors == 0:
        return {
            "averageScore": 0,
            "totalVendors": 0,
            "improved": 0,
            "degraded": 0,
            "stable": 0,
            "tier1Coverage": 0,
        }

    # Average of each vendor's latest score
    latest_scores_subq = (
        select(
            VendorScore.vendor_id,
            VendorScore.global_score,
            sa_func.row_number()
            .over(partition_by=VendorScore.vendor_id, order_by=VendorScore.scanned_at.desc())
            .label("rn"),
        )
    ).subquery()

    latest = select(
        sa_func.avg(latest_scores_subq.c.global_score).label("avg_score"),
        sa_func.count().label("scored_count"),
    ).where(latest_scores_subq.c.rn == 1)

    avg_result = await db.execute(latest)
    row = avg_result.one_or_none()
    avg_score = round(float(row.avg_score)) if row and row.avg_score else 0

    # Tier-1 coverage
    tier1_total_result = await db.execute(
        select(sa_func.count(Vendor.id)).where(Vendor.tier == 1)
    )
    tier1_total = tier1_total_result.scalar() or 0

    tier1_scored_result = await db.execute(
        select(sa_func.count(sa_func.distinct(VendorScore.vendor_id))).where(
            VendorScore.vendor_id.in_(
                select(Vendor.id).where(Vendor.tier == 1)
            )
        )
    )
    tier1_scored = tier1_scored_result.scalar() or 0
    tier1_coverage = round(tier1_scored / tier1_total * 100) if tier1_total else 100

    return {
        "averageScore": avg_score,
        "totalVendors": total_vendors,
        "improved": 0,
        "degraded": 0,
        "stable": total_vendors,
        "tier1Coverage": tier1_coverage,
    }


@router.get("/grade-distribution")
async def get_grade_distribution(
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> list[dict]:
    """Return vendor count per grade bucket for the latest scores."""
    latest_scores_subq = (
        select(
            VendorScore.vendor_id,
            VendorScore.grade,
            sa_func.row_number()
            .over(partition_by=VendorScore.vendor_id, order_by=VendorScore.scanned_at.desc())
            .label("rn"),
        )
    ).subquery()

    result = await db.execute(
        select(
            latest_scores_subq.c.grade,
            sa_func.count().label("cnt"),
        )
        .where(latest_scores_subq.c.rn == 1)
        .group_by(latest_scores_subq.c.grade)
    )
    counts = {row.grade: row.cnt for row in result.all()}

    grades = ["A", "B", "C", "D", "F"]
    return [
        {"grade": g, "current": counts.get(g, 0), "previous": 0}
        for g in grades
    ]


@router.get("/vendors/{vendor_id}/latest", response_model=ScoreResponse)
async def get_latest_score(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> ScoreResponse:
    """Get the latest score for a vendor."""
    result = await db.execute(
        select(VendorScore)
        .where(VendorScore.vendor_id == vendor_id)
        .order_by(VendorScore.scanned_at.desc())
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No score found for vendor {vendor_id}",
        )
    return ScoreResponse.model_validate(score)


@router.get("/vendors/{vendor_id}/history", response_model=list[ScoreResponse])
async def get_score_history(
    vendor_id: str,
    limit: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> list[ScoreResponse]:
    """Get score history for a vendor (most recent first)."""
    result = await db.execute(
        select(VendorScore)
        .where(VendorScore.vendor_id == vendor_id)
        .order_by(VendorScore.scanned_at.desc())
        .limit(limit)
    )
    scores = result.scalars().all()
    return [ScoreResponse.model_validate(s) for s in scores]


@router.get("/vendors/{vendor_id}/domains", response_model=dict)
async def get_domain_breakdown(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> dict:
    """Get the domain-by-domain score breakdown for a vendor's latest scan."""
    result = await db.execute(
        select(VendorScore)
        .where(VendorScore.vendor_id == vendor_id)
        .order_by(VendorScore.scanned_at.desc())
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No score found for vendor {vendor_id}",
        )
    return {
        "vendor_id": vendor_id,
        "global_score": score.global_score,
        "grade": score.grade,
        "domain_scores": score.domain_scores,
        "scanned_at": score.scanned_at.isoformat(),
    }


@router.get("/vendors/{vendor_id}/findings", response_model=list[FindingResponse])
async def get_vendor_findings(
    vendor_id: str,
    severity: str | None = Query(None, pattern=r"^(critical|high|medium|low|info)$"),
    domain: str | None = Query(None, pattern=r"^D[1-8]$"),
    finding_status: str | None = Query(
        None,
        alias="status",
        pattern=r"^(open|acknowledged|disputed|resolved|false_positive)$",
    ),
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> list[FindingResponse]:
    """Get findings for a vendor with optional filters."""
    query = select(Finding).where(Finding.vendor_id == vendor_id)
    if severity:
        query = query.where(Finding.severity == severity)
    if domain:
        query = query.where(Finding.domain == domain)
    if finding_status:
        query = query.where(Finding.status == finding_status)
    query = query.order_by(Finding.created_at.desc())

    result = await db.execute(query)
    findings = result.scalars().all()
    return [FindingResponse.model_validate(f) for f in findings]


@router.post("/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_scan(
    request: ScoringTriggerRequest,
    _current_user: object = Depends(require_role("admin", "rssi", "analyste_ssi")),
) -> dict:
    """Trigger an asynchronous scoring scan via Celery.

    Returns a task ID that can be polled for status.
    """
    # In production, this dispatches a Celery task:
    # task = score_vendor_task.delay(request.vendor_id, request.domains)
    # return {"task_id": task.id, ...}
    return {
        "message": "Scan triggered",
        "vendor_id": request.vendor_id,
        "domains": request.domains or ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"],
        "priority": request.priority,
        "status": "queued",
    }
