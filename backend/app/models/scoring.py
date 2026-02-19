"""Scoring ORM models: VendorScore and Finding."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VendorScore(Base):
    """Aggregated vendor cyber score at a point in time."""

    __tablename__ = "vendor_scores"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    vendor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vendors.id", ondelete="CASCADE"), index=True
    )
    global_score: Mapped[int] = mapped_column(
        comment="Global score 0-1000"
    )
    grade: Mapped[str] = mapped_column(
        String(1), comment="Grade A-F"
    )
    domain_scores: Mapped[dict] = mapped_column(
        JSONB, default=dict, comment="Per-domain score breakdown"
    )
    scan_id: Mapped[str | None] = mapped_column(String(36))
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    vendor: Mapped["Vendor"] = relationship(back_populates="scores")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<VendorScore(id={self.id!r}, vendor_id={self.vendor_id!r}, "
            f"score={self.global_score}, grade={self.grade!r})>"
        )


class Finding(Base):
    """Individual security finding from an OSINT scan."""

    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    vendor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vendors.id", ondelete="CASCADE"), index=True
    )
    scan_id: Mapped[str | None] = mapped_column(String(36), index=True)
    domain: Mapped[str] = mapped_column(
        String(10), comment="Scoring domain D1-D8"
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(
        String(20), index=True,
        comment="critical | high | medium | low | info",
    )
    cvss_score: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(100))
    evidence: Mapped[str | None] = mapped_column(Text)
    recommendation: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), default="open", index=True,
        comment="open | acknowledged | disputed | resolved | false_positive",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    vendor: Mapped["Vendor"] = relationship(back_populates="findings")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Finding(id={self.id!r}, domain={self.domain!r}, "
            f"severity={self.severity!r}, title={self.title!r})>"
        )
