"""Vendor CRUD endpoints."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.schemas.vendor import (
    VendorCreate,
    VendorListResponse,
    VendorResponse,
    VendorUpdate,
)
from app.services.vendor_service import VendorService
from app.utils.exceptions import VendorAlreadyExistsError, VendorNotFoundError

router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.get("/", response_model=VendorListResponse)
async def list_vendors(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tier: int | None = Query(None, ge=1, le=3, description="Filter by tier"),
    industry: str | None = Query(None, description="Filter by industry"),
    grade: str | None = Query(None, pattern=r"^[A-F]$", description="Filter by grade"),
    status_filter: str | None = Query(
        None, alias="status", pattern=r"^(active|inactive|under_review)$"
    ),
    search: str | None = Query(None, description="Search by name or domain"),
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> VendorListResponse:
    """List vendors with pagination and optional filters."""
    service = VendorService(db)
    return await service.list_vendors(
        page=page,
        page_size=page_size,
        tier=tier,
        industry=industry,
        grade=grade,
        status=status_filter,
        search=search,
    )


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> VendorResponse:
    """Get a single vendor by ID."""
    service = VendorService(db)
    try:
        return await service.get_vendor(vendor_id)
    except VendorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor not found: {vendor_id}",
        )


@router.post("/", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor: VendorCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(require_role("admin", "rssi", "analyste_ssi")),
) -> VendorResponse:
    """Create a new vendor."""
    service = VendorService(db)
    try:
        return await service.create_vendor(vendor)
    except VendorAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A vendor with domain '{vendor.domain}' already exists",
        )


@router.patch("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: str,
    vendor: VendorUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(require_role("admin", "rssi", "analyste_ssi")),
) -> VendorResponse:
    """Update an existing vendor."""
    service = VendorService(db)
    try:
        return await service.update_vendor(vendor_id, vendor)
    except VendorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor not found: {vendor_id}",
        )


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(require_role("admin")),
) -> None:
    """Delete a vendor (admin only)."""
    service = VendorService(db)
    try:
        await service.delete_vendor(vendor_id)
    except VendorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor not found: {vendor_id}",
        )


@router.post("/{vendor_id}/rescan", status_code=status.HTTP_202_ACCEPTED)
async def rescan_vendor(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(require_role("admin", "rssi", "analyste_ssi")),
) -> dict:
    """Trigger a rescan for a specific vendor."""
    service = VendorService(db)
    try:
        await service.get_vendor(vendor_id)
    except VendorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor not found: {vendor_id}",
        )
    task_id = str(uuid4())
    return {
        "vendor_id": vendor_id,
        "task_id": task_id,
        "status": "queued",
        "message": "Rescan triggered",
    }
