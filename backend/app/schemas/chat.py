"""Chat Pydantic schemas for CyberChat RAG."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatSource(BaseModel):
    """A source reference attached to a chat answer."""

    type: str = Field(..., description="score | finding | document | vendor")
    id: str
    title: str
    relevance: float = Field(default=1.0, ge=0.0, le=1.0)


class ChatMessageRequest(BaseModel):
    """Incoming chat message from user."""

    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    """AI response with sourced citations."""

    id: str
    answer: str
    sources: list[ChatSource] = []
    content: str = ""
    conversation_id: str
    timestamp: datetime


class ChatHistoryItem(BaseModel):
    """A single item in chat history."""

    id: str
    role: str = Field(..., description="user | assistant")
    content: str
    sources: list[ChatSource] = []
    timestamp: datetime


class ChatHistoryResponse(BaseModel):
    """Chat history list."""

    conversation_id: str
    messages: list[ChatHistoryItem]


class IndexRequest(BaseModel):
    """Request to trigger RAG reindex."""

    collections: list[str] = Field(
        default=["scores", "findings", "documents"],
        description="Collections to reindex",
    )
