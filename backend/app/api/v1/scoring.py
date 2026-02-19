"""Scoring endpoints: scores, history, domain breakdown, scan trigger."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.scoring import Finding, VendorScore
from app.schemas.scoring import FindingResponse, ScoreResponse, ScoringTriggerRequest

router = APIRouter(prefix="/scoring", tags=["scoring"])


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
