"""Schemas for the vendor self-service portal."""

from datetime import datetime

from pydantic import BaseModel, Field


class PortalScorecard(BaseModel):
    """Vendor's scorecard visible in the portal."""

    vendor_id: str
    vendor_name: str
    domain: str
    score: int = Field(..., ge=0, le=1000)
    grade: str
    domain_scores: dict[str, int] = Field(default_factory=dict)
    last_scan: datetime | None = None


class PortalFinding(BaseModel):
    """A finding visible to the vendor."""

    id: str
    title: str
    severity: str
    domain: str
    status: str = "open"
    description: str = ""
    detected_at: datetime | None = None


class PortalDisputeCreate(BaseModel):
    """Request to dispute a finding."""

    finding_id: str
    reason: str = Field(..., min_length=10, max_length=2000)
    contact_email: str = ""


class PortalDispute(BaseModel):
    """A dispute record."""

    id: str
    finding_id: str
    reason: str
    status: str = "pending"
    created_at: datetime | None = None
    evidence_urls: list[str] = Field(default_factory=list)


class EvidenceUpload(BaseModel):
    """Metadata for uploaded evidence."""

    dispute_id: str
    filename: str
    content_type: str
    size_bytes: int
    url: str


class PortalQuestionnaire(BaseModel):
    """A questionnaire assigned to the vendor."""

    id: str
    title: str
    status: str = "pending"
    due_date: datetime | None = None
    question_count: int = 0


class QuestionnaireResponse(BaseModel):
    """Vendor's responses to a questionnaire."""

    answers: dict[str, str] = Field(
        ..., description="Mapping of question_id to answer text"
    )
