"""Questionnaire API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.schemas.questionnaire import (
    QuestionnaireCreateRequest,
    QuestionnaireListItem,
    QuestionnaireResponse,
    QuestionnaireSendRequest,
    QuestionnaireSendResponse,
    QuestionnaireSubmitRequest,
    QuestionnaireSubmitResponse,
    QuestionnaireTemplateInfo,
    SmartAnswerRequest,
    SmartAnswerResponse,
)
from app.services.questionnaire_service import QuestionnaireService

router = APIRouter(prefix="/questionnaires", tags=["questionnaires"])


@router.get("/templates", response_model=list[QuestionnaireTemplateInfo])
async def list_templates(
    _current_user: object = Depends(get_current_user),
) -> list[QuestionnaireTemplateInfo]:
    """List available questionnaire templates."""
    # Templates are static, no DB needed
    from app.services.questionnaire_service import QuestionnaireService as QS

    service = QS.__new__(QS)
    return service.list_templates()


@router.post("/", response_model=QuestionnaireResponse, status_code=status.HTTP_201_CREATED)
async def create_questionnaire(
    data: QuestionnaireCreateRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(require_role("admin", "rssi", "analyste_ssi")),
) -> QuestionnaireResponse:
    """Create a questionnaire from a template."""
    service = QuestionnaireService(db)
    try:
        return await service.create_from_template(data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get("/", response_model=list[QuestionnaireListItem])
async def list_questionnaires(
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> list[QuestionnaireListItem]:
    """List all questionnaires."""
    service = QuestionnaireService(db)
    return await service.list_questionnaires()


@router.get("/{questionnaire_id}", response_model=QuestionnaireResponse)
async def get_questionnaire(
    questionnaire_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> QuestionnaireResponse:
    """Get a questionnaire with its questions."""
    service = QuestionnaireService(db)
    try:
        return await service.get_questionnaire(questionnaire_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Questionnaire not found: {questionnaire_id}",
        )


@router.post("/{questionnaire_id}/send", response_model=QuestionnaireSendResponse)
async def send_questionnaire(
    questionnaire_id: str,
    data: QuestionnaireSendRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(require_role("admin", "rssi", "analyste_ssi")),
) -> QuestionnaireSendResponse:
    """Send a questionnaire to a vendor contact."""
    service = QuestionnaireService(db)
    try:
        return await service.send_questionnaire(questionnaire_id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.post("/{questionnaire_id}/respond", response_model=QuestionnaireSubmitResponse)
async def submit_response(
    questionnaire_id: str,
    data: QuestionnaireSubmitRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> QuestionnaireSubmitResponse:
    """Submit answers to a questionnaire."""
    service = QuestionnaireService(db)
    return await service.submit_response(questionnaire_id, data.vendor_id, data.answers)


@router.post("/{questionnaire_id}/smart-answer", response_model=SmartAnswerResponse)
async def smart_answer(
    questionnaire_id: str,
    data: SmartAnswerRequest,
    db: AsyncSession = Depends(get_db),
    _current_user: object = Depends(get_current_user),
) -> SmartAnswerResponse:
    """Get an AI-generated answer suggestion for a question."""
    service = QuestionnaireService(db)
    try:
        return await service.smart_answer_suggestion(questionnaire_id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
