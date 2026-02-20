"""Questionnaire Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ── Templates ───────────────────────────────────────────────────────────

class QuestionnaireTemplateInfo(BaseModel):
    """Summary of an available questionnaire template."""

    name: str
    description: str
    category: str
    question_count: int


# ── Questionnaire CRUD ──────────────────────────────────────────────────

class QuestionnaireCreateRequest(BaseModel):
    """Create a questionnaire from a template for a vendor."""

    template_name: str = Field(..., description="Template key: RGPD, DORA, ISO27001, NIST_CSF, HDS")
    vendor_id: str
    title: str | None = None


class QuestionnaireResponse(BaseModel):
    """Full questionnaire response."""

    id: str
    title: str
    description: str | None
    version: str
    category: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    questions: list["QuestionResponse"] = []

    model_config = {"from_attributes": True}


class QuestionResponse(BaseModel):
    """Individual question in a questionnaire."""

    id: str
    questionnaire_id: str
    order: int
    text: str
    question_type: str
    options: dict | None
    is_required: bool
    weight: float | None
    category: str | None

    model_config = {"from_attributes": True}


class QuestionnaireListItem(BaseModel):
    """Summary item for questionnaire list."""

    id: str
    title: str
    category: str | None
    version: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Send / Respond ──────────────────────────────────────────────────────

class QuestionnaireSendRequest(BaseModel):
    """Send a questionnaire to a vendor contact."""

    vendor_id: str
    recipient_email: EmailStr


class QuestionnaireSendResponse(BaseModel):
    """Response after sending a questionnaire."""

    response_id: str
    questionnaire_id: str
    vendor_id: str
    status: str
    message: str


class AnswerSubmission(BaseModel):
    """A single answer in a questionnaire submission."""

    question_id: str
    value: str


class QuestionnaireSubmitRequest(BaseModel):
    """Submit answers to a questionnaire."""

    vendor_id: str
    answers: list[AnswerSubmission]


class QuestionnaireSubmitResponse(BaseModel):
    """Response after submitting answers."""

    response_id: str
    status: str
    score: float | None
    message: str


# ── Smart Answer ────────────────────────────────────────────────────────

class SmartAnswerRequest(BaseModel):
    """Request for AI-generated answer suggestion."""

    question_id: str
    vendor_context: str | None = Field(None, description="Additional context about the vendor")


class SmartAnswerResponse(BaseModel):
    """AI-generated answer suggestion."""

    question_id: str
    suggested_answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str | None = None


# Resolve forward references
QuestionnaireResponse.model_rebuild()
