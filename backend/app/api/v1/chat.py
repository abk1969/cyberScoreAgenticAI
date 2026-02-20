"""Chat API — CyberChat RAG-powered AI assistant endpoints."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import UserClaims, get_current_user, get_db
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageRequest,
    ChatResponse,
    ChatSource,
    IndexRequest,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    user: UserClaims = Depends(get_current_user),
) -> ChatResponse:
    """Send a message to CyberChat and get an AI response with sources.

    Uses RAG to search relevant context from vendor scores, findings,
    and documents before generating the response.
    """
    from app.agents.chat_agent import ChatAgent

    conversation_id = request.conversation_id or str(uuid4())

    agent = ChatAgent()
    result = await agent.execute(
        vendor_id="",
        message=request.message,
        user_id=user.sub,
        conversation_id=conversation_id,
    )

    # Extract sources from context if available
    sources: list[ChatSource] = []
    data = result.data
    context_chunks = data.get("context_chunks_used", 0)
    if context_chunks > 0 and "sources" in data:
        for src in data["sources"]:
            sources.append(ChatSource(
                type=src.get("type", "document"),
                id=src.get("id", ""),
                title=src.get("title", ""),
                relevance=src.get("relevance", 1.0),
            ))

    answer = data.get("response", "")

    return ChatResponse(
        id=str(uuid4()),
        answer=answer,
        content=answer,
        sources=sources,
        conversation_id=conversation_id,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    conversation_id: str = "",
    _user: UserClaims = Depends(get_current_user),
) -> ChatHistoryResponse:
    """Get chat history for a conversation.

    Returns an empty list if no history exists (chat is ephemeral
    until persistent storage is implemented).
    """
    return ChatHistoryResponse(
        conversation_id=conversation_id or str(uuid4()),
        messages=[],
    )


@router.post("/index")
async def trigger_reindex(
    request: IndexRequest,
    db: AsyncSession = Depends(get_db),
    _user: UserClaims = Depends(get_current_user),
) -> dict:
    """Trigger RAG reindexing of specified collections.

    Fetches data from DB and indexes into Qdrant vector store.
    """
    from app.config import settings
    from app.models.scoring import Finding, VendorScore
    from app.models.vendor import Vendor
    from app.services.llm_provider import LLMProviderConfig, get_llm_provider
    from app.services.rag_service import RAGService

    from sqlalchemy import select

    # Initialize RAG service
    qdrant_url = settings.redis_url.replace("redis://", "http://").replace(":6379", ":6333")
    llm = get_llm_provider(LLMProviderConfig(
        provider=settings.llm_default_provider,
        model_name=settings.llm_default_model,
    ))
    rag = RAGService(qdrant_url=qdrant_url, llm_provider=llm)

    indexed = {}

    if "scores" in request.collections:
        scores_q = select(VendorScore).order_by(VendorScore.scanned_at.desc())
        score_result = await db.execute(scores_q)
        scores = score_result.scalars().all()

        # Fetch vendor names
        vendor_q = select(Vendor)
        vendor_result = await db.execute(vendor_q)
        vendors = {v.id: v.name for v in vendor_result.scalars().all()}

        score_dicts = [
            {
                "vendor_id": s.vendor_id,
                "vendor_name": vendors.get(s.vendor_id, ""),
                "global_score": s.global_score,
                "grade": s.grade,
                "domain_scores": s.domain_scores or {},
            }
            for s in scores
        ]
        indexed["scores"] = await rag.index_vendor_scores(score_dicts)

    if "findings" in request.collections:
        findings_q = select(Finding)
        finding_result = await db.execute(findings_q)
        findings = finding_result.scalars().all()

        finding_dicts = [
            {
                "id": f.id,
                "vendor_id": f.vendor_id,
                "title": f.title,
                "description": f.description or "",
                "severity": f.severity,
                "domain": f.domain,
            }
            for f in findings
        ]
        indexed["findings"] = await rag.index_findings(finding_dicts)

    return {
        "status": "completed",
        "indexed": indexed,
        "collections": request.collections,
    }
