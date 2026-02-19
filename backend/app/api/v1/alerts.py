"""Alert endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.alert import Alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/")
async def list_alerts(
    vendor_id: str | None = Query(None),
    severity: str | None = Query(None, pattern=r"^(critical|high|medium|low|info)$"),
    is_read: bool | None = Query(None),
    is_resolved: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> dict:
    """List alerts with optional filters and pagination."""
    query = select(Alert)
    if vendor_id:
        query = query.where(Alert.vendor_id == vendor_id)
    if severity:
        query = query.where(Alert.severity == severity)
    if is_read is not None:
        query = query.where(Alert.is_read == is_read)
    if is_resolved is not None:
        query = query.where(Alert.is_resolved == is_resolved)

    query = query.order_by(Alert.created_at.desc())

    # Count total
    from sqlalchemy import func as sa_func

    count_query = select(sa_func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    alerts = result.scalars().all()

    return {
        "items": [
            {
                "id": a.id,
                "vendor_id": a.vendor_id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "description": a.description,
                "is_read": a.is_read,
                "is_resolved": a.is_resolved,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.get("/{alert_id}")
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> dict:
    """Get a single alert by ID."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert not found: {alert_id}",
        )
    return {
        "id": alert.id,
        "vendor_id": alert.vendor_id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "title": alert.title,
        "description": alert.description,
        "is_read": alert.is_read,
        "is_resolved": alert.is_resolved,
        "created_at": alert.created_at.isoformat(),
    }


@router.patch("/{alert_id}/read")
async def mark_alert_read(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> dict:
    """Mark an alert as read."""
    result = await db.execute(
        update(Alert).where(Alert.id == alert_id).values(is_read=True).returning(Alert.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert not found: {alert_id}",
        )
    return {"message": "Alert marked as read", "alert_id": alert_id}


@router.patch("/{alert_id}/resolve")
async def mark_alert_resolved(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> dict:
    """Mark an alert as resolved."""
    result = await db.execute(
        update(Alert)
        .where(Alert.id == alert_id)
        .values(is_resolved=True)
        .returning(Alert.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert not found: {alert_id}",
        )
    return {"message": "Alert marked as resolved", "alert_id": alert_id}
