from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.schemas.rag import Citation


class ConversationInfo(BaseModel):
    id: str
    user_id: str
    kb_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    conversations: list[ConversationInfo]
    count: int


class MessageInfo(BaseModel):
    id: str
    conversation_id: str
    role: str  # "user" | "assistant"
    content: str
    citations: Optional[list[Citation]] = None
    created_at: datetime


class ConversationDetailResponse(BaseModel):
    conversation: ConversationInfo
    messages: list[MessageInfo]


class DeleteConversationResponse(BaseModel):
    id: str
    status: str