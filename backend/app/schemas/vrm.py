"""VRM Pydantic schemas for disputes and remediation plans."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


# ── Onboarding ──────────────────────────────────────────────────────────

class VendorOnboardRequest(BaseModel):
    """Schema for onboarding a new vendor via VRM workflow."""

    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=3, max_length=255)
    industry: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    employee_count: int | None = Field(None, ge=0)
    contract_value: Decimal | None = Field(None, ge=0)
    contact_email: EmailStr | None = None
    description: str | None = None


class VendorOnboardResponse(BaseModel):
    """Response after vendor onboarding."""

    id: str
    name: str
    domain: str
    tier: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Disputes ────────────────────────────────────────────────────────────

class DisputeCreate(BaseModel):
    """Schema for creating a dispute against a finding."""

    finding_id: str = Field(..., min_length=1)
    evidence_url: str | None = Field(None, max_length=500)
    requester_email: EmailStr


class DisputeUpdate(BaseModel):
    """Schema for updating/resolving a dispute."""

    status: str = Field(..., pattern=r"^(in_review|resolved|rejected)$")
    admin_notes: str | None = None


class DisputeResponse(BaseModel):
    """Dispute API response."""

    id: str
    vendor_id: str
    finding_id: str
    status: str
    evidence_url: str | None
    requester_email: str
    admin_notes: str | None
    sla_deadline: datetime
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


# ── Remediation ─────────────────────────────────────────────────────────

class RemediationCreate(BaseModel):
    """Schema for creating a remediation plan item."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=1)
    priority: str = Field(default="medium", pattern=r"^(critical|high|medium|low)$")
    deadline: datetime
    assigned_to: str | None = Field(None, max_length=255)


class RemediationResponse(BaseModel):
    """Remediation plan item API response."""

    id: str
    vendor_id: str
    title: str
    description: str
    priority: str
    deadline: datetime
    status: str
    assigned_to: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
