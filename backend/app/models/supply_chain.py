"""Supply Chain ORM models for Nth-party dependency tracking."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VendorDependency(Base):
    """Nth-party dependency record linking a vendor to an infrastructure provider."""

    __tablename__ = "vendor_dependencies"
    __table_args__ = (
        Index("ix_vendor_dep_vendor_provider", "vendor_id", "provider_name"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    vendor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vendors.id", ondelete="CASCADE"), index=True
    )
    provider_name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    provider_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="cloud | cdn | dns | email | cert",
    )
    dependency_tier: Mapped[int] = mapped_column(
        default=1, comment="1=direct, 2=indirect, 3=deep"
    )
    detected_via: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="dns | tls | headers | legal",
    )
    confidence: Mapped[float] = mapped_column(
        Float, default=0.8, comment="Detection confidence 0.0-1.0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ConcentrationAlert(Base):
    """Alert raised when provider concentration exceeds threshold."""

    __tablename__ = "concentration_alerts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    provider_name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    dependent_count: Mapped[int] = mapped_column(
        nullable=False, comment="Number of vendors depending on this provider"
    )
    percentage: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Concentration percentage 0.0-1.0"
    )
    risk_level: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="low | medium | high | critical",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
