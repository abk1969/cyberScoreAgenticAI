"""Questionnaire ORM models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Questionnaire(Base):
    """Assessment questionnaire template."""

    __tablename__ = "questionnaires"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    category: Mapped[str | None] = mapped_column(
        String(100), comment="e.g. dora, iso27001, custom"
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    questions: Mapped[list["Question"]] = relationship(
        back_populates="questionnaire", lazy="selectin",
    )
    responses: Mapped[list["QuestionnaireResponse"]] = relationship(
        back_populates="questionnaire", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Questionnaire(id={self.id!r}, title={self.title!r})>"


class Question(Base):
    """Individual question within a questionnaire."""

    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    questionnaire_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questionnaires.id", ondelete="CASCADE"), index=True
    )
    order: Mapped[int] = mapped_column(default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(
        String(50), default="text",
        comment="text | single_choice | multi_choice | scale | file_upload",
    )
    options: Mapped[dict | None] = mapped_column(JSONB, comment="Choices for single/multi_choice")
    is_required: Mapped[bool] = mapped_column(default=True)
    weight: Mapped[float | None] = mapped_column(comment="Scoring weight for this question")
    category: Mapped[str | None] = mapped_column(String(100))

    # Relationships
    questionnaire: Mapped["Questionnaire"] = relationship(back_populates="questions")

    def __repr__(self) -> str:
        return f"<Question(id={self.id!r}, text={self.text[:50]!r})>"


class QuestionnaireResponse(Base):
    """A vendor's response to a full questionnaire."""

    __tablename__ = "questionnaire_responses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    questionnaire_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questionnaires.id", ondelete="CASCADE"), index=True
    )
    vendor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vendors.id", ondelete="CASCADE"), index=True
    )
    submitted_by: Mapped[str | None] = mapped_column(String(36))
    status: Mapped[str] = mapped_column(
        String(20), default="draft",
        comment="draft | submitted | reviewed | approved | rejected",
    )
    score: Mapped[float | None] = mapped_column(comment="Computed score for this response")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    questionnaire: Mapped["Questionnaire"] = relationship(back_populates="responses")
    answers: Mapped[list["Answer"]] = relationship(
        back_populates="response", lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<QuestionnaireResponse(id={self.id!r}, vendor_id={self.vendor_id!r}, "
            f"status={self.status!r})>"
        )


class Answer(Base):
    """Individual answer to a question."""

    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    response_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questionnaire_responses.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    value: Mapped[str | None] = mapped_column(Text)
    file_path: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    response: Mapped["QuestionnaireResponse"] = relationship(back_populates="answers")

    def __repr__(self) -> str:
        return f"<Answer(id={self.id!r}, question_id={self.question_id!r})>"
