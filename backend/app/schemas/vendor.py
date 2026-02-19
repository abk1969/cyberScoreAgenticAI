"""Vendor Pydantic schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import PaginatedResponse


class VendorBase(BaseModel):
    """Shared vendor fields."""

    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=3, max_length=255)
    tier: int = Field(default=3, ge=1, le=3, description="1=critical, 2=important, 3=standard")
    industry: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    employee_count: int | None = Field(None, ge=0)
    contract_value: Decimal | None = Field(None, ge=0)
    description: str | None = None
    website: str | None = Field(None, max_length=500)
    contact_email: EmailStr | None = None


class VendorCreate(VendorBase):
    """Schema for creating a new vendor."""


class VendorUpdate(BaseModel):
    """Schema for updating a vendor (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    domain: str | None = Field(None, min_length=3, max_length=255)
    tier: int | None = Field(None, ge=1, le=3)
    industry: str | None = Field(None, max_length=100)
    country: str | None = Field(None, max_length=100)
    employee_count: int | None = Field(None, ge=0)
    contract_value: Decimal | None = Field(None, ge=0)
    description: str | None = None
    website: str | None = Field(None, max_length=500)
    contact_email: EmailStr | None = None
    status: str | None = Field(None, pattern=r"^(active|inactive|under_review)$")


class VendorResponse(VendorBase):
    """Schema for vendor API responses."""

    id: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VendorListResponse(PaginatedResponse[VendorResponse]):
    """Paginated vendor list response."""
