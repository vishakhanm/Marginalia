"""
Embedding service — wraps Ollama's embedding endpoint.

Kept separate from kb_service because the RAG retrieval service (Step 6)
will also need to embed text (the user's query), and both should share
this exact logic rather than duplicating it.
"""

from app.core.db import get_ollama_client
from app.core.config import get_settings

settings = get_settings()


def embed_text(text: str) -> list[float]:
    """Return the embedding vector for a single piece of text."""
    client = get_ollama_client()
    response = client.embeddings(model=settings.default_embedding_model, prompt=text)
    return response["embedding"]


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed multiple texts. Ollama's embeddings API is called once per text
    (no native batch endpoint in the client) — fine for playground-scale
    ingestion; worth revisiting with concurrency if ingesting large corpora.
    """
    return [embed_text(t) for t in texts]