"""GRC ORM models: SecurityControl, FrameworkMapping, MaturityAssessment."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SecurityControl(Base):
    """A security control tracked for GRC/PSSI compliance."""

    __tablename__ = "security_controls"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    reference: Mapped[str] = mapped_column(
        String(50), unique=True, comment="Control reference code (e.g. CTL-001)"
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(
        String(100), index=True,
        comment="Control domain (e.g. access_control, network_security)",
    )
    status: Mapped[str] = mapped_column(
        String(20), default="not_implemented", index=True,
        comment="implemented | partial | not_implemented",
    )
    owner: Mapped[str | None] = mapped_column(String(200))
    evidence_url: Mapped[str | None] = mapped_column(String(1000))
    last_assessed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # Relationships
    framework_mappings: Mapped[list["FrameworkMapping"]] = relationship(
        back_populates="control", cascade="all, delete-orphan"
    )
    maturity_assessments: Mapped[list["MaturityAssessment"]] = relationship(
        back_populates="control", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<SecurityControl(ref={self.reference!r}, "
            f"domain={self.domain!r}, status={self.status!r})>"
        )


class FrameworkMapping(Base):
    """Maps a security control to a regulatory framework requirement."""

    __tablename__ = "framework_mappings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    control_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("security_controls.id", ondelete="CASCADE"), index=True
    )
    framework: Mapped[str] = mapped_column(
        String(20), index=True,
        comment="iso27001 | dora | nis2 | hds | rgpd",
    )
    framework_ref: Mapped[str] = mapped_column(
        String(50), comment="Framework-specific reference (e.g. A.9.1.1)"
    )
    description: Mapped[str | None] = mapped_column(Text)

    # Relationships
    control: Mapped["SecurityControl"] = relationship(
        back_populates="framework_mappings"
    )

    def __repr__(self) -> str:
        return (
            f"<FrameworkMapping(framework={self.framework!r}, "
            f"ref={self.framework_ref!r})>"
        )


class MaturityAssessment(Base):
    """Maturity assessment for a security control (CMMI level 1-5)."""

    __tablename__ = "maturity_assessments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    control_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("security_controls.id", ondelete="CASCADE"), index=True
    )
    level: Mapped[int] = mapped_column(
        Integer, comment="Maturity level 1-5 (CMMI)"
    )
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    assessor: Mapped[str] = mapped_column(
        String(200), comment="Person or system that performed the assessment"
    )

    # Relationships
    control: Mapped["SecurityControl"] = relationship(
        back_populates="maturity_assessments"
    )

    def __repr__(self) -> str:
        return (
            f"<MaturityAssessment(control_id={self.control_id!r}, "
            f"level={self.level})>"
        )
