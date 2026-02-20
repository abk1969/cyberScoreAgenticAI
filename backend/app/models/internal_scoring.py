"""Internal Scoring ORM models: InternalScan and InternalFinding."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InternalScan(Base):
    """An internal infrastructure scan (AD, M365, or GRC assessment)."""

    __tablename__ = "internal_scans"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    scan_type: Mapped[str] = mapped_column(
        String(10), index=True,
        comment="ad | m365 | grc",
    )
    target: Mapped[str] = mapped_column(
        String(500), comment="Domain controller, tenant ID, or GRC scope"
    )
    score: Mapped[int] = mapped_column(
        Integer, default=0, comment="Score 0-1000"
    )
    grade: Mapped[str] = mapped_column(
        String(1), default="F", comment="Grade A-F"
    )
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    scan_data: Mapped[dict] = mapped_column(
        JSONB, default=dict, comment="Full scan results JSON"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    findings: Mapped[list["InternalFinding"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<InternalScan(id={self.id!r}, type={self.scan_type!r}, "
            f"score={self.score}, grade={self.grade!r})>"
        )


class InternalFinding(Base):
    """Individual finding from an internal scan."""

    __tablename__ = "internal_findings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    scan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("internal_scans.id", ondelete="CASCADE"), index=True
    )
    category: Mapped[str] = mapped_column(
        String(100), index=True,
        comment="Finding category (e.g. privileged_accounts, gpo_security)",
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(
        String(20), index=True,
        comment="critical | high | medium | low | info",
    )
    recommendation: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), default="open", index=True,
        comment="open | resolved",
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    scan: Mapped["InternalScan"] = relationship(back_populates="findings")

    def __repr__(self) -> str:
        return (
            f"<InternalFinding(id={self.id!r}, category={self.category!r}, "
            f"severity={self.severity!r}, title={self.title!r})>"
        )
