"""LLM Configuration ORM model."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LLMConfig(Base):
    """Stores LLM provider configuration with encrypted API keys.

    Only ONE config should be active at a time (is_active=True).
    """

    __tablename__ = "llm_configs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="mistral|gemini|claude|openai|ollama",
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    api_key_encrypted: Mapped[str | None] = mapped_column(
        Text, comment="AES-256-GCM encrypted API key"
    )
    api_base_url: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<LLMConfig(id={self.id!r}, provider={self.provider!r}, "
            f"model={self.model_name!r}, active={self.is_active})>"
        )
