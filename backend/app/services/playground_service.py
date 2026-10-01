"""
Playground service — direct chat with any local model, no knowledge base
and no persistence. Deliberately bypasses rag_service, history_service,
and config_service entirely: nothing here touches Mongo. The caller sends
the full message list each turn since there's no server-side state to
append to.
"""

from app.core.db import get_ollama_client
from app.schemas.playground import PlaygroundMessage, PlaygroundChatResponse


def generate_playground_response(
    messages: list[PlaygroundMessage],
    model: str,
    temperature: float,
    preamble: str | None,
) -> PlaygroundChatResponse:
    ollama_messages = []
    if preamble:
        ollama_messages.append({"role": "system", "content": preamble})
    ollama_messages.extend({"role": m.role, "content": m.content} for m in messages)

    client = get_ollama_client()
    response = client.chat(
        model=model,
        messages=ollama_messages,
        options={"temperature": temperature},
    )
    return PlaygroundChatResponse(answer=response["message"]["content"], model=model)