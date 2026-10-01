from pydantic import BaseModel, Field
from typing import Optional


class ModelInfo(BaseModel):
    """A single locally available Ollama model."""
    name: str
    size_bytes: Optional[int] = None
    parameter_size: Optional[str] = None
    quantization: Optional[str] = None
    modified_at: Optional[str] = None
    is_protected: bool = False


class ModelListResponse(BaseModel):
    models: list[ModelInfo]
    count: int


class PullModelRequest(BaseModel):
    name: str = Field(..., description="Model tag to pull, e.g. 'llama3.2' or 'nomic-embed-text'")


class PullModelResponse(BaseModel):
    name: str
    status: str
    detail: Optional[str] = None


class DeleteModelResponse(BaseModel):
    name: str
    status: str