"""Scoring Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class DomainScoreResponse(BaseModel):
    """Score for a single scoring domain (D1-D8)."""

    domain: str = Field(..., description="Domain identifier D1-D8")
    domain_name: str = Field(..., description="Human-readable domain name")
    score: float = Field(..., ge=0, le=100)
    grade: str = Field(..., description="A-E grade")
    finding_count: int = Field(default=0, ge=0)


class ScoreResponse(BaseModel):
    """Vendor score API response."""

    id: str
    vendor_id: str
    global_score: int = Field(..., ge=0, le=1000)
    grade: str = Field(..., description="A-F grade")
    domain_scores: dict
    scan_id: str | None = None
    scanned_at: datetime

    model_config = {"from_attributes": True}


class FindingResponse(BaseModel):
    """Finding API response."""

    id: str
    vendor_id: str
    scan_id: str | None
    domain: str
    title: str
    description: str | None
    severity: str
    cvss_score: float | None
    source: str | None
    evidence: str | None
    recommendation: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScoringTriggerRequest(BaseModel):
    """Request to trigger a new vendor scoring scan."""

    vendor_id: str
    domains: list[str] | None = Field(
        None, description="Specific domains to scan (D1-D8). None = all domains."
    )
    priority: str = Field(
        default="normal", pattern=r"^(low|normal|high|critical)$"
    )
