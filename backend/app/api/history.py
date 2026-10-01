from fastapi import APIRouter, HTTPException, Depends

from app.schemas.history import (
    ConversationListResponse,
    ConversationDetailResponse,
    DeleteConversationResponse,
)
from app.services import history_service
from app.core.security import get_current_user

router = APIRouter()


@router.get("", response_model=ConversationListResponse)
def list_conversations(current_user: dict = Depends(get_current_user)):
    """List the current user's conversations, most recently updated first."""
    return history_service.list_conversations(current_user["_id"])


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Fetch a conversation's full message history. Only the owner can view it."""
    result = history_service.get_conversation(conversation_id, current_user["_id"])
    if result is None:
        raise HTTPException(status_code=404, detail=f"Conversation '{conversation_id}' not found")
    return result


@router.delete("/{conversation_id}", response_model=DeleteConversationResponse)
def delete_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a conversation and its messages. Only the owner can delete it."""
    return history_service.delete_conversation(conversation_id, current_user["_id"])