"""GRC/PSSI Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class SecurityControlResponse(BaseModel):
    """Security control API response."""

    id: str
    reference: str
    title: str
    description: str | None
    domain: str
    status: str
    owner: str | None
    evidence_url: str | None
    last_assessed: datetime | None
    frameworks: list[str] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class SecurityControlUpdate(BaseModel):
    """Request to update a security control."""

    status: str | None = Field(
        None, pattern=r"^(implemented|partial|not_implemented)$"
    )
    owner: str | None = None
    evidence_url: str | None = None


class FrameworkCoverage(BaseModel):
    """Coverage summary for a single framework."""

    framework: str
    total_controls: int
    implemented: int
    partial: int
    not_implemented: int
    coverage_percent: float = Field(..., ge=0, le=100)


class MaturityData(BaseModel):
    """Maturity data for a control or domain."""

    domain: str
    average_level: float = Field(..., ge=0, le=5)
    control_count: int
    levels: dict[int, int] = Field(
        default_factory=dict,
        description="Count of controls at each maturity level (1-5)",
    )


class HeatmapCell(BaseModel):
    """Single cell in the GRC heatmap."""

    domain: str
    framework: str
    coverage_percent: float = Field(..., ge=0, le=100)
    status: str = Field(..., description="good | warning | critical")
