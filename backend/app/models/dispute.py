"""Dispute ORM model for vendor finding disputes."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Dispute(Base):
    """Vendor dispute against a security finding."""

    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    vendor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vendors.id", ondelete="CASCADE"), index=True
    )
    finding_id: Mapped[str] = mapped_column(String(36), index=True)
    status: Mapped[str] = mapped_column(
        String(20), default="open", index=True,
        comment="open | in_review | resolved | rejected",
    )
    evidence_url: Mapped[str | None] = mapped_column(String(500))
    requester_email: Mapped[str] = mapped_column(String(255), nullable=False)
    admin_notes: Mapped[str | None] = mapped_column(Text)
    sla_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return (
            f"<Dispute(id={self.id!r}, vendor_id={self.vendor_id!r}, "
            f"status={self.status!r})>"
        )
