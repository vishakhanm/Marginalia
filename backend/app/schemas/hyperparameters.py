from pydantic import BaseModel, Field
from typing import Optional


class HyperparameterSettings(BaseModel):
    """
    A partial or full set of tunable hyperparameters. All fields optional
    so this same shape works for global config, KB-level overrides, and
    per-request overrides — at each layer only the fields someone actually
    set are populated, and the rest fall through to the next layer.
    """
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_k: Optional[int] = Field(None, ge=1, le=20)
    chunk_size: Optional[int] = Field(None, gt=0)
    chunk_overlap: Optional[int] = Field(None, ge=0)
    preamble: Optional[str] = None


class GlobalConfigResponse(BaseModel):
    model: str
    temperature: float
    top_k: int
    chunk_size: int
    chunk_overlap: int
    preamble: str


class UpdateGlobalConfigRequest(HyperparameterSettings):
    """Same shape as HyperparameterSettings — any subset of fields can be updated."""
    pass