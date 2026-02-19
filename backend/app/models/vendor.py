"""Vendor ORM model."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import DateTime, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Vendor(Base):
    """Third-party vendor entity tracked for cyber scoring."""

    __tablename__ = "vendors"
    __table_args__ = (
        Index("ix_vendors_tier_status", "tier", "status"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    tier: Mapped[int] = mapped_column(default=3, comment="1=critical, 2=important, 3=standard")
    industry: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    employee_count: Mapped[int | None] = mapped_column()
    contract_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2))
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(500))
    contact_email: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(20), default="active", index=True,
        comment="active | inactive | under_review",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    scores: Mapped[list["VendorScore"]] = relationship(  # noqa: F821
        back_populates="vendor", lazy="selectin",
    )
    findings: Mapped[list["Finding"]] = relationship(  # noqa: F821
        back_populates="vendor", lazy="selectin",
    )
    alerts: Mapped[list["Alert"]] = relationship(  # noqa: F821
        back_populates="vendor", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Vendor(id={self.id!r}, name={self.name!r}, domain={self.domain!r})>"
