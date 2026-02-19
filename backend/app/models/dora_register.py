"""DORA Register ORM model (art. 28 compliance)."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DORARegisterEntry(Base):
    """DORA art. 28 ICT third-party register entry for ACPR reporting."""

    __tablename__ = "dora_register"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    vendor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vendors.id", ondelete="CASCADE"), index=True
    )

    # Identification
    vendor_name: Mapped[str] = mapped_column(String(255))
    vendor_type: Mapped[str] = mapped_column(
        String(100), comment="ICT service type"
    )
    contract_reference: Mapped[str] = mapped_column(String(100))

    # Criticality
    is_critical: Mapped[bool] = mapped_column(default=False)
    criticality_justification: Mapped[str | None] = mapped_column(Text)

    # Service details
    service_description: Mapped[str] = mapped_column(Text)
    data_types_processed: Mapped[list] = mapped_column(JSONB, default=list)
    data_locations: Mapped[list] = mapped_column(
        JSONB, default=list, comment="Countries where data is processed"
    )

    # Subcontracting
    subcontractors: Mapped[list] = mapped_column(JSONB, default=list)
    subcontracting_chain_mapped: Mapped[bool] = mapped_column(default=False)

    # Risk assessment
    last_risk_assessment_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    risk_score: Mapped[int | None] = mapped_column()

    # Exit strategy
    exit_plan_exists: Mapped[bool] = mapped_column(default=False)
    exit_plan_last_tested: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Compliance
    certifications: Mapped[list] = mapped_column(
        JSONB, default=list, comment="e.g. ISO 27001, HDS, SOC2"
    )
    last_audit_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<DORARegisterEntry(id={self.id!r}, vendor={self.vendor_name!r}, "
            f"critical={self.is_critical})>"
        )
