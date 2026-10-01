from fastapi import APIRouter, HTTPException, Depends

from app.schemas.rag import ChatRequest, ChatResponse
from app.services import rag_service, history_service
from app.core.security import get_current_user

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Ask a question against a knowledge base and get a cited answer.
    Every exchange is recorded to the caller's chat history — either
    appended to `conversation_id` if provided, or starting a new
    conversation otherwise.
    """
    try:
        result = rag_service.generate_answer(
            kb_id=request.kb_id,
            query=request.query,
            model=request.model,
            temperature=request.temperature,
            top_k=request.top_k,
            preamble=request.preamble,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    conversation = history_service.save_exchange(
        user_id=current_user["_id"],
        kb_id=request.kb_id,
        conversation_id=request.conversation_id,
        query=request.query,
        response=result,
    )
    result.conversation_id = conversation.id
    return result