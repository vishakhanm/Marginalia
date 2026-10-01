from fastapi import APIRouter, HTTPException

from app.schemas.model import (
    ModelListResponse,
    PullModelRequest,
    PullModelResponse,
    DeleteModelResponse,
)
from app.services import model_service

router = APIRouter()


@router.get("", response_model=ModelListResponse)
def get_models():
    """List all locally available Ollama models."""
    return model_service.list_models()


@router.post("/pull", response_model=PullModelResponse)
def pull_model(request: PullModelRequest):
    """Pull a model from the Ollama registry. Blocks until the pull completes."""
    result = model_service.pull_model(request.name)
    if result.status == "error":
        raise HTTPException(status_code=502, detail=result.detail or "Failed to pull model")
    return result


@router.delete("/{name}", response_model=DeleteModelResponse)
def delete_model(name: str):
    try:
        result = model_service.delete_model(name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if result.status == "error":
        raise HTTPException(status_code=404, detail=f"Could not delete model '{name}'")
    return result