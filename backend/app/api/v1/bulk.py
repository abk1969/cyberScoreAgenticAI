"""Bulk operations API — CSV import, batch scan, data export."""

import csv
import io
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.scoring import Finding, VendorScore
from app.models.vendor import Vendor
from app.schemas.bulk import (
    BulkExportFormat,
    BulkImportResult,
    BulkScanRequest,
    BulkScanResponse,
)

router = APIRouter(prefix="/bulk", tags=["bulk"])


@router.post("/vendors", response_model=BulkImportResult)
async def bulk_import_vendors(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(require_role("admin", "rssi")),
) -> BulkImportResult:
    """Import vendors from a CSV file.

    CSV format: name,domain,tier,industry,country,contact_email
    First row must be a header row.
    """
    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    created = 0
    skipped = 0
    errors: list[str] = []
    total = 0

    for row_num, row in enumerate(reader, start=2):
        total += 1
        name = row.get("name", "").strip()
        domain = row.get("domain", "").strip()

        if not name or not domain:
            errors.append(f"Row {row_num}: missing name or domain")
            continue

        # Check duplicate
        existing = await db.execute(
            select(Vendor).where(Vendor.domain == domain)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        try:
            tier = int(row.get("tier", "3"))
        except ValueError:
            tier = 3

        vendor = Vendor(
            name=name,
            domain=domain,
            tier=max(1, min(3, tier)),
            industry=row.get("industry", "").strip() or None,
            country=row.get("country", "").strip() or None,
            contact_email=row.get("contact_email", "").strip() or None,
        )
        db.add(vendor)
        created += 1

    return BulkImportResult(
        total_rows=total,
        created=created,
        skipped=skipped,
        errors=errors,
    )


@router.post("/scan", response_model=BulkScanResponse)
async def bulk_scan(
    request: BulkScanRequest,
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(require_role("admin", "rssi", "analyste_ssi")),
) -> BulkScanResponse:
    """Trigger batch scanning for multiple vendors.

    If vendor_ids is empty, scans all active vendors.
    """
    from app.agents.osint_agent import scan_vendor_osint

    if request.vendor_ids:
        vendor_q = select(Vendor).where(Vendor.id.in_(request.vendor_ids))
    else:
        vendor_q = select(Vendor).where(Vendor.status == "active")

    result = await db.execute(vendor_q)
    vendors = result.scalars().all()

    queued_ids: list[str] = []
    for v in vendors:
        scan_vendor_osint.delay(v.id, v.domain)
        queued_ids.append(v.id)

    return BulkScanResponse(
        total_queued=len(queued_ids),
        vendor_ids=queued_ids,
        scan_type=request.scan_type,
    )


@router.get("/export")
async def bulk_export(
    format: BulkExportFormat = Query(BulkExportFormat.JSON),
    db: AsyncSession = Depends(get_db),
    _user: object = Depends(get_current_user),
) -> StreamingResponse:
    """Export all vendor data with scores and findings.

    Supports CSV and JSON formats.
    """
    # Fetch data
    vendor_result = await db.execute(select(Vendor))
    vendors = vendor_result.scalars().all()

    score_result = await db.execute(
        select(VendorScore).order_by(VendorScore.scanned_at.desc())
    )
    scores = score_result.scalars().all()
    score_map: dict[str, VendorScore] = {}
    for s in scores:
        if s.vendor_id not in score_map:
            score_map[s.vendor_id] = s

    finding_result = await db.execute(select(Finding).where(Finding.status == "open"))
    findings = finding_result.scalars().all()
    finding_counts: dict[str, int] = {}
    for f in findings:
        finding_counts[f.vendor_id] = finding_counts.get(f.vendor_id, 0) + 1

    # Build rows
    rows: list[dict] = []
    for v in vendors:
        sc = score_map.get(v.id)
        rows.append({
            "vendor_id": v.id,
            "name": v.name,
            "domain": v.domain,
            "tier": v.tier,
            "industry": v.industry or "",
            "country": v.country or "",
            "status": v.status,
            "global_score": sc.global_score if sc else "",
            "grade": sc.grade if sc else "",
            "scanned_at": sc.scanned_at.isoformat() if sc and sc.scanned_at else "",
            "open_findings": finding_counts.get(v.id, 0),
        })

    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if format == BulkExportFormat.CSV:
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        content = output.getvalue()
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="export_{now}.csv"'
            },
        )

    # JSON format
    content = json.dumps(rows, indent=2, default=str)
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="export_{now}.json"'
        },
    )
