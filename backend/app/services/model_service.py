"""
Model management service — thin wrapper around the Ollama client for
listing, pulling, and deleting locally available models.

Kept separate from the API layer so routes stay thin and this logic
is unit-testable without spinning up FastAPI.
"""

import logging
from ollama import ResponseError

from app.core.db import get_ollama_client
from app.schemas.model import (
    ModelInfo,
    ModelListResponse,
    PullModelResponse,
    DeleteModelResponse,
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def list_models() -> ModelListResponse:
    """Return all models currently pulled/available in the local Ollama instance."""
    client = get_ollama_client()
    response = client.list()

    models = []
    for m in response.get("models", []):
        details = m.get("details", {}) or {}
        models.append(
            ModelInfo(
                name=m.get("model") or m.get("name"),
                size_bytes=m.get("size"),
                parameter_size=details.get("parameter_size"),
                quantization=details.get("quantization_level"),
                modified_at=str(m.get("modified_at")) if m.get("modified_at") else None,
            )
        )

    return ModelListResponse(models=models, count=len(models))

def _is_protected(name: str) -> bool:
    """The default chat model and embedding model can't be deleted — the app
    depends on them being present for /chat and /knowledge uploads to work."""
    protected = {settings.default_model, settings.default_embedding_model}
    # Ollama model names are often tagged ("llama3.2:latest") while config
    # may store them untagged ("llama3.2") — match on the base name too.
    base_name = name.split(":")[0]
    return name in protected or base_name in protected

def pull_model(name: str) -> PullModelResponse:
    """
    Pull a model from the Ollama registry. This can take a while for large
    models — Ollama streams progress internally, but we wait for completion
    and return a single status here (streaming progress to the client is a
    future enhancement).
    """
    client = get_ollama_client()
    try:
        client.pull(model=name)
        logger.info(f"Successfully pulled model: {name}")
        return PullModelResponse(name=name, status="success")
    except ResponseError as e:
        logger.error(f"Failed to pull model {name}: {e}")
        return PullModelResponse(name=name, status="error", detail=str(e))


def delete_model(name: str) -> DeleteModelResponse:
    if _is_protected(name):
        raise ValueError(
            f"'{name}' is the default chat or embedding model and can't be deleted. "
            f"Change the default in Config first if you want to remove it."
        )
    client = get_ollama_client()
    try:
        client.delete(model=name)
        return DeleteModelResponse(name=name, status="success")
    except ResponseError:
        return DeleteModelResponse(name=name, status="error")