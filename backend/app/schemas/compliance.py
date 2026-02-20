"""Schemas for DORA compliance register and gap analysis."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class DORARegisterEntry(BaseModel):
    """A single entry in the DORA ICT provider register (Art. 28)."""

    id: str
    vendor_id: str
    vendor_name: str
    service_type: str = ""
    critical: bool = False
    tier: int = Field(3, ge=1, le=3)
    contract_start: date | None = None
    contract_end: date | None = None
    last_audit: date | None = None
    score: int = Field(0, ge=0, le=1000)
    grade: str = "F"
    compliance_status: str = "non-conforme"
    notes: str = ""


class DORARegisterCreate(BaseModel):
    """Create or update a DORA register entry."""

    vendor_id: str
    service_type: str = ""
    critical: bool = False
    tier: int = Field(3, ge=1, le=3)
    contract_start: date | None = None
    contract_end: date | None = None
    notes: str = ""


class DORAcoverage(BaseModel):
    """DORA register coverage statistics."""

    total_vendors: int = 0
    registered: int = 0
    coverage_pct: float = 0.0
    critical_count: int = 0
    tier1_count: int = 0
    tier2_count: int = 0
    tier3_count: int = 0
    evaluated_this_quarter: int = 0
    last_updated: datetime | None = None


class DORAGap(BaseModel):
    """A gap identified in DORA compliance."""

    id: str
    vendor_id: str
    vendor_name: str
    gap_type: str
    description: str
    severity: str = "medium"
    recommendation: str = ""


class DORAExportRequest(BaseModel):
    """Options for exporting the DORA register."""

    format: str = "xlsx"
    include_gaps: bool = True
    include_coverage: bool = True
