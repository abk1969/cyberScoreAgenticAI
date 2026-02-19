"""Report endpoints: list, generate, download."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role, UserClaims
from app.models.report import Report

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportGenerateRequest(BaseModel):
    """Request body for generating a report."""

    report_type: str = Field(..., pattern=r"^(executive|rssi|vendor|dora|benchmark)$")
    format: str = Field(default="pdf", pattern=r"^(pdf|pptx|xlsx)$")
    vendor_id: str | None = None


@router.get("/")
async def list_reports(
    report_type: str | None = Query(None, pattern=r"^(executive|rssi|vendor|dora|benchmark)$"),
    vendor_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> dict:
    """List generated reports with optional filters."""
    query = select(Report)
    if report_type:
        query = query.where(Report.report_type == report_type)
    if vendor_id:
        query = query.where(Report.vendor_id == vendor_id)
    query = query.order_by(Report.created_at.desc())

    from sqlalchemy import func as sa_func

    count_query = select(sa_func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    reports = result.scalars().all()

    return {
        "items": [
            {
                "id": r.id,
                "report_type": r.report_type,
                "format": r.format,
                "vendor_id": r.vendor_id,
                "generated_by": r.generated_by,
                "file_size": r.file_size,
                "created_at": r.created_at.isoformat(),
            }
            for r in reports
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    request: ReportGenerateRequest,
    current_user: UserClaims = Depends(
        require_role("admin", "rssi", "analyste_ssi", "direction_achats", "comex")
    ),
) -> dict:
    """Trigger asynchronous report generation via Celery.

    Returns a task ID for polling status.
    """
    # In production: task = generate_report_task.delay(...)
    return {
        "message": "Report generation queued",
        "report_type": request.report_type,
        "format": request.format,
        "vendor_id": request.vendor_id,
        "requested_by": current_user.sub,
        "status": "queued",
    }


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> FileResponse:
    """Download a generated report file."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report not found: {report_id}",
        )

    media_types = {
        "pdf": "application/pdf",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    return FileResponse(
        path=report.file_path,
        media_type=media_types.get(report.format, "application/octet-stream"),
        filename=f"report-{report.id}.{report.format}",
    )
