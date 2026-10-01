from fastapi import APIRouter, HTTPException

from app.schemas.endpoint import (
    CreateEndpointRequest,
    EndpointInfo,
    EndpointListResponse,
    DeleteEndpointResponse,
)
from app.services import endpoint_service

router = APIRouter()


@router.post("", response_model=EndpointInfo)
def create_endpoint(request: CreateEndpointRequest):
    """Publish a new on-demand inference endpoint for a knowledge base + hyperparameter combo."""
    return endpoint_service.create_endpoint(request.name, request.kb_id, request.hyperparameters)


@router.get("", response_model=EndpointListResponse)
def list_endpoints():
    """List all published endpoints."""
    return endpoint_service.list_endpoints()


@router.get("/{endpoint_id}", response_model=EndpointInfo)
def get_endpoint(endpoint_id: str):
    """Fetch details (and usage stats) for a single published endpoint."""
    endpoint = endpoint_service.get_endpoint(endpoint_id)
    if endpoint is None:
        raise HTTPException(status_code=404, detail=f"Endpoint '{endpoint_id}' not found")
    return endpoint


@router.delete("/{endpoint_id}", response_model=DeleteEndpointResponse)
def delete_endpoint(endpoint_id: str):
    """Unpublish an endpoint."""
    return endpoint_service.delete_endpoint(endpoint_id)