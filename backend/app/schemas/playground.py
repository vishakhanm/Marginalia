from pydantic import BaseModel, Field
from typing import Optional, Literal


class PlaygroundMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class PlaygroundChatRequest(BaseModel):
    """
    Nothing here is ever persisted. The frontend holds the running message
    list itself (since there's no server-side conversation to append to) and
    resends it each turn — same shape as a stateless chat completion call.
    """
    messages: list[PlaygroundMessage] = Field(..., min_length=1)
    model: str
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    preamble: Optional[str] = Field(None, description="Optional system prompt")


class PlaygroundChatResponse(BaseModel):
    answer: str
    model: str