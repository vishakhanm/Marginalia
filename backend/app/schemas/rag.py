from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    kb_id: str = Field(..., description="Knowledge base to retrieve context from")
    query: str = Field(..., description="The user's question")
    model: Optional[str] = Field(None, description="Ollama model to use; falls back to config default")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_k: Optional[int] = Field(None, ge=1, le=20, description="Number of chunks to retrieve")
    preamble: Optional[str] = Field(None, description="System instruction override")
    conversation_id: Optional[str] = Field(
        None, description="Continue an existing conversation; omit to start a new one"
    )


class Citation(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    text_snippet: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    model: str
    kb_id: str
    conversation_id: Optional[str] = None