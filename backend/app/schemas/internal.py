"""Internal scoring Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ADScanConfig(BaseModel):
    """Configuration for an Active Directory scan."""

    domain_controller: str = Field(..., description="Domain controller hostname or IP")
    credentials: dict = Field(
        default_factory=dict,
        description="Auth credentials (username, password or keytab path)",
    )
    threshold_dormant_days: int = Field(
        default=90, ge=1, description="Days since last login to flag as dormant"
    )


class M365ScanConfig(BaseModel):
    """Configuration for a Microsoft 365 scan."""

    tenant_id: str = Field(..., description="Azure AD tenant ID")
    credentials: dict = Field(
        default_factory=dict,
        description="Auth credentials (client_id, client_secret or certificate)",
    )


class InternalScanCreate(BaseModel):
    """Request to create an internal scan."""

    scan_type: str = Field(..., pattern=r"^(ad|m365|grc)$")
    target: str = Field(..., min_length=1, max_length=500)
    config: dict = Field(default_factory=dict)


class InternalScanResponse(BaseModel):
    """Internal scan API response."""

    id: str
    scan_type: str
    target: str
    score: int = Field(..., ge=0, le=1000)
    grade: str
    findings_count: int
    scan_data: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class InternalFindingResponse(BaseModel):
    """Internal finding API response."""

    id: str
    scan_id: str
    category: str
    title: str
    description: str | None
    severity: str
    recommendation: str | None
    status: str
    detected_at: datetime

    model_config = {"from_attributes": True}
