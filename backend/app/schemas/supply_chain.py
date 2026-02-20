"""Supply Chain Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class SupplyChainNode(BaseModel):
    """A node in the supply chain dependency graph."""

    id: str
    name: str
    type: str = Field(..., description="vendor | provider | subcontractor")
    tier: int = Field(default=1, ge=1, le=3)
    score: int | None = None
    grade: str | None = None
    provider_type: str | None = Field(None, description="cloud | cdn | dns | email | cert")


class SupplyChainLink(BaseModel):
    """An edge in the supply chain dependency graph."""

    source: str
    target: str
    type: str = Field(default="direct", description="direct | indirect")
    detected_via: str | None = None
    confidence: float | None = None


class GraphData(BaseModel):
    """Full supply chain graph for D3.js rendering."""

    nodes: list[SupplyChainNode]
    links: list[SupplyChainLink]


class ConcentrationRisk(BaseModel):
    """Concentration risk for a single provider."""

    provider_name: str
    dependent_count: int
    percentage: float = Field(..., ge=0.0, le=1.0)
    risk_level: str = Field(..., description="low | medium | high | critical")
    created_at: datetime | None = None


class ConcentrationRiskResponse(BaseModel):
    """Full concentration risk analysis response."""

    threshold: float
    risks: list[ConcentrationRisk]
    total_vendors: int
    total_providers: int


class VendorDependencyResponse(BaseModel):
    """A vendor's dependency record."""

    id: str
    vendor_id: str
    provider_name: str
    provider_type: str
    dependency_tier: int
    detected_via: str
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyzeRequest(BaseModel):
    """Request to trigger supply chain analysis."""

    vendor_ids: list[str] = Field(..., min_length=1, description="Vendor IDs to analyze")
