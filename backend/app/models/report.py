"""Report ORM model."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Report(Base):
    """Generated report (PDF, PPTX, XLSX)."""

    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    report_type: Mapped[str] = mapped_column(
        String(20), index=True,
        comment="executive | rssi | vendor | dora | benchmark",
    )
    format: Mapped[str] = mapped_column(
        String(10), comment="pdf | pptx | xlsx",
    )
    vendor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("vendors.id", ondelete="SET NULL"), index=True
    )
    generated_by: Mapped[str] = mapped_column(String(36), comment="User ID who requested")
    file_path: Mapped[str] = mapped_column(String(500))
    file_size: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<Report(id={self.id!r}, type={self.report_type!r}, "
            f"format={self.format!r})>"
        )
