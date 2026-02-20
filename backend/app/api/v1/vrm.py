"""VRM (Vendor Risk Management) API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.schemas.vrm import (
    DisputeCreate,
    DisputeResponse,
    DisputeUpdate,
    RemediationCreate,
    RemediationResponse,
    VendorOnboardRequest,
    VendorOnboardResponse,
)
from app.services.vrm_service import VRMService
from app.utils.exceptions import VendorAlreadyExistsError, VendorNotFoundError

router = APIRouter(prefix="/vrm", tags=["vrm"])


@router.post("/onboard", response_model=VendorOnboardResponse, status_code=status.HTTP_201_CREATED)
async def onboard_vendor(
    data: VendorOnboardRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(require_role("admin", "rssi", "analyste_ssi")),
) -> VendorOnboardResponse:
    """Onboard a new vendor via the VRM workflow with auto-tiering."""
    service = VRMService(db)
    try:
        return await service.onboard_vendor(data)
    except VendorAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A vendor with domain '{data.domain}' already exists",
        )


@router.post(
    "/vendors/{vendor_id}/dispute",
    response_model=DisputeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_dispute(
    vendor_id: str,
    data: DisputeCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> DisputeResponse:
    """Create a dispute against a finding for a vendor."""
    service = VRMService(db)
    try:
        return await service.create_dispute(vendor_id, data)
    except VendorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor not found: {vendor_id}",
        )


@router.get("/disputes", response_model=list[DisputeResponse])
async def list_disputes(
    vendor_id: str | None = Query(None, description="Filter by vendor ID"),
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> list[DisputeResponse]:
    """List all disputes, optionally filtered by vendor."""
    service = VRMService(db)
    return await service.list_disputes(vendor_id=vendor_id)


@router.put("/disputes/{dispute_id}", response_model=DisputeResponse)
async def resolve_dispute(
    dispute_id: str,
    data: DisputeUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(require_role("admin", "rssi", "analyste_ssi")),
) -> DisputeResponse:
    """Update or resolve a dispute (admin/RSSI only)."""
    service = VRMService(db)
    try:
        return await service.resolve_dispute(dispute_id, data)
    except VendorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute not found: {dispute_id}",
        )


@router.post(
    "/vendors/{vendor_id}/remediation",
    response_model=RemediationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_remediation(
    vendor_id: str,
    data: RemediationCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(require_role("admin", "rssi", "analyste_ssi")),
) -> RemediationResponse:
    """Create a remediation plan item for a vendor."""
    service = VRMService(db)
    try:
        return await service.create_remediation_plan(vendor_id, data)
    except VendorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vendor not found: {vendor_id}",
        )


@router.get("/vendors/{vendor_id}/remediation", response_model=list[RemediationResponse])
async def list_remediations(
    vendor_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> list[RemediationResponse]:
    """List remediation plan items for a vendor."""
    service = VRMService(db)
    return await service.list_remediations(vendor_id)
