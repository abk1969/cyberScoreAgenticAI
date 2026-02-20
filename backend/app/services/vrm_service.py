"""VRM (Vendor Risk Management) business logic service."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dispute import Dispute
from app.models.remediation import Remediation
from app.models.scoring import Finding
from app.models.vendor import Vendor
from app.schemas.vrm import (
    DisputeCreate,
    DisputeResponse,
    DisputeUpdate,
    RemediationCreate,
    RemediationResponse,
    VendorOnboardRequest,
    VendorOnboardResponse,
)
from app.utils.exceptions import VendorAlreadyExistsError, VendorNotFoundError


# SLA deadlines by vendor tier (days)
_SLA_DAYS = {1: 5, 2: 10, 3: 20}

# Auto-tier thresholds based on contract value
_TIER_THRESHOLDS = [
    (500_000, 1),   # >= 500k => Tier 1 (critical)
    (100_000, 2),   # >= 100k => Tier 2 (important)
    (0, 3),         # default  => Tier 3 (standard)
]


class VRMService:
    """Service layer for VRM workflows: onboarding, disputes, remediation."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Onboarding ──────────────────────────────────────────────────

    async def onboard_vendor(self, data: VendorOnboardRequest) -> VendorOnboardResponse:
        """Onboard a new vendor with auto-tiering.

        Args:
            data: Vendor onboarding data.

        Returns:
            Onboarded vendor response.

        Raises:
            VendorAlreadyExistsError: If domain is already registered.
        """
        existing = await self.db.execute(
            select(Vendor).where(Vendor.domain == data.domain)
        )
        if existing.scalar_one_or_none():
            raise VendorAlreadyExistsError(data.domain)

        vendor = Vendor(
            name=data.name,
            domain=data.domain,
            industry=data.industry,
            country=data.country,
            employee_count=data.employee_count,
            contract_value=data.contract_value,
            contact_email=data.contact_email,
            description=data.description,
            status="active",
        )

        # Auto-tier based on contract value
        vendor.tier = self._auto_tier(vendor)

        self.db.add(vendor)
        await self.db.flush()
        await self.db.refresh(vendor)
        return VendorOnboardResponse.model_validate(vendor)

    @staticmethod
    def _auto_tier(vendor: Vendor) -> int:
        """Determine vendor tier based on contract value.

        Args:
            vendor: Vendor entity.

        Returns:
            Tier value 1-3.
        """
        cv = float(vendor.contract_value or 0)
        for threshold, tier in _TIER_THRESHOLDS:
            if cv >= threshold:
                return tier
        return 3

    async def auto_tier_vendor(self, vendor_id: str) -> VendorOnboardResponse:
        """Re-compute tier for an existing vendor.

        Args:
            vendor_id: Vendor UUID.

        Returns:
            Updated vendor response.
        """
        result = await self.db.execute(
            select(Vendor).where(Vendor.id == vendor_id)
        )
        vendor = result.scalar_one_or_none()
        if not vendor:
            raise VendorNotFoundError(vendor_id)

        vendor.tier = self._auto_tier(vendor)
        await self.db.flush()
        await self.db.refresh(vendor)
        return VendorOnboardResponse.model_validate(vendor)

    async def start_monitoring(self, vendor_id: str, schedule: str = "default") -> dict:
        """Start continuous monitoring for a vendor.

        Args:
            vendor_id: Vendor UUID.
            schedule: Monitoring schedule name.

        Returns:
            Monitoring status dict.
        """
        result = await self.db.execute(
            select(Vendor).where(Vendor.id == vendor_id)
        )
        vendor = result.scalar_one_or_none()
        if not vendor:
            raise VendorNotFoundError(vendor_id)

        # Mark as active and schedule scan via Celery (import at runtime)
        vendor.status = "active"
        await self.db.flush()

        return {
            "vendor_id": vendor_id,
            "schedule": schedule,
            "tier": vendor.tier,
            "status": "monitoring_started",
        }

    # ── Disputes ────────────────────────────────────────────────────

    async def create_dispute(
        self, vendor_id: str, data: DisputeCreate
    ) -> DisputeResponse:
        """Create a dispute against a finding.

        Args:
            vendor_id: Vendor UUID.
            data: Dispute creation data.

        Returns:
            Created dispute response.
        """
        result = await self.db.execute(
            select(Vendor).where(Vendor.id == vendor_id)
        )
        vendor = result.scalar_one_or_none()
        if not vendor:
            raise VendorNotFoundError(vendor_id)

        sla_days = _SLA_DAYS.get(vendor.tier, 20)
        dispute = Dispute(
            vendor_id=vendor_id,
            finding_id=data.finding_id,
            evidence_url=data.evidence_url,
            requester_email=data.requester_email,
            sla_deadline=datetime.now(timezone.utc) + timedelta(days=sla_days),
        )
        self.db.add(dispute)
        await self.db.flush()
        await self.db.refresh(dispute)
        return DisputeResponse.model_validate(dispute)

    async def list_disputes(self, vendor_id: str | None = None) -> list[DisputeResponse]:
        """List disputes, optionally filtered by vendor.

        Args:
            vendor_id: Optional vendor UUID filter.

        Returns:
            List of dispute responses.
        """
        query = select(Dispute).order_by(Dispute.created_at.desc())
        if vendor_id:
            query = query.where(Dispute.vendor_id == vendor_id)
        result = await self.db.execute(query)
        disputes = result.scalars().all()
        return [DisputeResponse.model_validate(d) for d in disputes]

    async def resolve_dispute(
        self, dispute_id: str, data: DisputeUpdate
    ) -> DisputeResponse:
        """Update/resolve a dispute.

        Args:
            dispute_id: Dispute UUID.
            data: Update data with new status and optional notes.

        Returns:
            Updated dispute response.

        Raises:
            VendorNotFoundError: If the dispute is not found.
        """
        result = await self.db.execute(
            select(Dispute).where(Dispute.id == dispute_id)
        )
        dispute = result.scalar_one_or_none()
        if not dispute:
            raise VendorNotFoundError(dispute_id)

        dispute.status = data.status
        if data.admin_notes is not None:
            dispute.admin_notes = data.admin_notes
        if data.status in ("resolved", "rejected"):
            dispute.resolved_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(dispute)
        return DisputeResponse.model_validate(dispute)

    # ── Remediation ─────────────────────────────────────────────────

    async def create_remediation_plan(
        self, vendor_id: str, data: RemediationCreate
    ) -> RemediationResponse:
        """Create a remediation plan item for a vendor.

        Args:
            vendor_id: Vendor UUID.
            data: Remediation item data.

        Returns:
            Created remediation response.
        """
        result = await self.db.execute(
            select(Vendor).where(Vendor.id == vendor_id)
        )
        if not result.scalar_one_or_none():
            raise VendorNotFoundError(vendor_id)

        remediation = Remediation(
            vendor_id=vendor_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            deadline=data.deadline,
            assigned_to=data.assigned_to,
        )
        self.db.add(remediation)
        await self.db.flush()
        await self.db.refresh(remediation)
        return RemediationResponse.model_validate(remediation)

    async def list_remediations(self, vendor_id: str) -> list[RemediationResponse]:
        """List remediation plan items for a vendor.

        Args:
            vendor_id: Vendor UUID.

        Returns:
            List of remediation responses.
        """
        query = (
            select(Remediation)
            .where(Remediation.vendor_id == vendor_id)
            .order_by(Remediation.created_at.desc())
        )
        result = await self.db.execute(query)
        items = result.scalars().all()
        return [RemediationResponse.model_validate(r) for r in items]
