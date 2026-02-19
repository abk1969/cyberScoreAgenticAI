"""Alert ORM model."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Alert(Base):
    """Real-time alert triggered by scoring events or threat intelligence."""

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    vendor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vendors.id", ondelete="CASCADE"), index=True
    )
    alert_type: Mapped[str] = mapped_column(
        String(50), index=True,
        comment="score_drop | new_vulnerability | breach | certificate_expiry | etc.",
    )
    severity: Mapped[str] = mapped_column(
        String(20), index=True,
        comment="critical | high | medium | low | info",
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(default=False)
    is_resolved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    # Relationships
    vendor: Mapped["Vendor"] = relationship(back_populates="alerts")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Alert(id={self.id!r}, type={self.alert_type!r}, "
            f"severity={self.severity!r}, title={self.title!r})>"
        )
