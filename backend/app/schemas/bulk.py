"""Bulk operations Pydantic schemas."""

from enum import Enum

from pydantic import BaseModel, Field


class BulkExportFormat(str, Enum):
    """Supported export formats."""

    CSV = "csv"
    JSON = "json"


class BulkImportRow(BaseModel):
    """A single row in a CSV import."""

    name: str
    domain: str
    tier: int = Field(default=3, ge=1, le=3)
    industry: str | None = None
    country: str | None = None
    contact_email: str | None = None


class BulkImportResult(BaseModel):
    """Result of a bulk vendor import."""

    total_rows: int
    created: int
    skipped: int
    errors: list[str]


class BulkScanRequest(BaseModel):
    """Request to trigger batch scanning."""

    vendor_ids: list[str] = Field(default=[], description="Specific vendor IDs; empty = all active")
    scan_type: str = Field(default="full", description="full | quick")


class BulkScanResponse(BaseModel):
    """Response after triggering batch scans."""

    total_queued: int
    vendor_ids: list[str]
    scan_type: str
