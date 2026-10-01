from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.schemas.hyperparameters import HyperparameterSettings


class CreateEndpointRequest(BaseModel):
    name: str = Field(..., description="Human-readable name, e.g. 'legal-contracts-qa'")
    kb_id: str = Field(..., description="Knowledge base this endpoint queries")
    hyperparameters: Optional[HyperparameterSettings] = Field(
        None, description="Hyperparameters locked into this endpoint; override the KB/global defaults"
    )


class EndpointInfo(BaseModel):
    id: str
    name: str
    kb_id: str
    hyperparameters: Optional[HyperparameterSettings] = None
    created_at: datetime
    call_count: int = 0
    last_called_at: Optional[datetime] = None


class EndpointListResponse(BaseModel):
    endpoints: list[EndpointInfo]
    count: int


class DeleteEndpointResponse(BaseModel):
    id: str
    status: str


class InvokeEndpointRequest(BaseModel):
    query: str = Field(..., description="The user's question — everything else is fixed by the endpoint config")