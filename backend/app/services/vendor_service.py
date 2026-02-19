"""Vendor business logic service."""

import math

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scoring import VendorScore
from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorListResponse, VendorResponse, VendorUpdate
from app.utils.exceptions import VendorAlreadyExistsError, VendorNotFoundError


class VendorService:
    """Service layer for vendor CRUD operations with filtering and pagination."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_vendor(self, vendor_id: str) -> VendorResponse:
        """Get a single vendor by ID.

        Args:
            vendor_id: The vendor UUID.

        Returns:
            Vendor response schema.

        Raises:
            VendorNotFoundError: If the vendor does not exist.
        """
        result = await self.db.execute(
            select(Vendor).where(Vendor.id == vendor_id)
        )
        vendor = result.scalar_one_or_none()
        if not vendor:
            raise VendorNotFoundError(vendor_id)
        return VendorResponse.model_validate(vendor)

    async def list_vendors(
        self,
        page: int = 1,
        page_size: int = 20,
        tier: int | None = None,
        industry: str | None = None,
        grade: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> VendorListResponse:
        """List vendors with pagination and filtering.

        Args:
            page: Page number (1-indexed).
            page_size: Items per page.
            tier: Filter by vendor tier (1-3).
            industry: Filter by industry.
            grade: Filter by latest score grade (A-F).
            status: Filter by vendor status.
            search: Full-text search on name and domain.

        Returns:
            Paginated vendor list response.
        """
        query = select(Vendor)

        # Apply filters
        if tier is not None:
            query = query.where(Vendor.tier == tier)
        if industry:
            query = query.where(Vendor.industry == industry)
        if status:
            query = query.where(Vendor.status == status)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(Vendor.name.ilike(pattern), Vendor.domain.ilike(pattern))
            )

        # Grade filter requires a subquery on latest score
        if grade:
            latest_score_subq = (
                select(
                    VendorScore.vendor_id,
                    func.max(VendorScore.scanned_at).label("max_scanned"),
                )
                .group_by(VendorScore.vendor_id)
                .subquery()
            )
            query = (
                query.join(
                    latest_score_subq,
                    Vendor.id == latest_score_subq.c.vendor_id,
                )
                .join(
                    VendorScore,
                    (VendorScore.vendor_id == latest_score_subq.c.vendor_id)
                    & (VendorScore.scanned_at == latest_score_subq.c.max_scanned),
                )
                .where(VendorScore.grade == grade)
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        query = query.order_by(Vendor.name).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        vendors = result.scalars().all()

        return VendorListResponse(
            items=[VendorResponse.model_validate(v) for v in vendors],
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total > 0 else 0,
        )

    async def create_vendor(self, data: VendorCreate) -> VendorResponse:
        """Create a new vendor.

        Args:
            data: Vendor creation data.

        Returns:
            Created vendor response.

        Raises:
            VendorAlreadyExistsError: If a vendor with the same domain already exists.
        """
        # Check for duplicate domain
        existing = await self.db.execute(
            select(Vendor).where(Vendor.domain == data.domain)
        )
        if existing.scalar_one_or_none():
            raise VendorAlreadyExistsError(data.domain)

        vendor = Vendor(**data.model_dump())
        self.db.add(vendor)
        await self.db.flush()
        await self.db.refresh(vendor)
        return VendorResponse.model_validate(vendor)

    async def update_vendor(self, vendor_id: str, data: VendorUpdate) -> VendorResponse:
        """Update an existing vendor.

        Args:
            vendor_id: The vendor UUID.
            data: Fields to update (only non-None fields are applied).

        Returns:
            Updated vendor response.

        Raises:
            VendorNotFoundError: If the vendor does not exist.
        """
        result = await self.db.execute(
            select(Vendor).where(Vendor.id == vendor_id)
        )
        vendor = result.scalar_one_or_none()
        if not vendor:
            raise VendorNotFoundError(vendor_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vendor, field, value)

        await self.db.flush()
        await self.db.refresh(vendor)
        return VendorResponse.model_validate(vendor)

    async def delete_vendor(self, vendor_id: str) -> None:
        """Delete a vendor by ID.

        Args:
            vendor_id: The vendor UUID.

        Raises:
            VendorNotFoundError: If the vendor does not exist.
        """
        result = await self.db.execute(
            select(Vendor).where(Vendor.id == vendor_id)
        )
        vendor = result.scalar_one_or_none()
        if not vendor:
            raise VendorNotFoundError(vendor_id)

        await self.db.delete(vendor)
        await self.db.flush()
