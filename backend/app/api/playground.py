from fastapi import APIRouter

from app.schemas.playground import PlaygroundChatRequest, PlaygroundChatResponse
from app.services import playground_service

router = APIRouter()


@router.post("/chat", response_model=PlaygroundChatResponse)
def playground_chat(request: PlaygroundChatRequest):
    """
    Free-form chat with any local model — no knowledge base, no saved
    hyperparameters, no chat history. Nothing from this endpoint is
    ever written to the database.
    """
    return playground_service.generate_playground_response(
        messages=request.messages,
        model=request.model,
        temperature=request.temperature,
        preamble=request.preamble,
    )