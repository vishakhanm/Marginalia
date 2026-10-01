from fastapi import APIRouter, HTTPException

from app.schemas.endpoint import InvokeEndpointRequest
from app.schemas.rag import ChatResponse
from app.services import endpoint_service

router = APIRouter()


@router.post("/{endpoint_id}", response_model=ChatResponse)
def invoke(endpoint_id: str, request: InvokeEndpointRequest):
    """
    Run inference against a published endpoint. This is the route external
    consumers call — they only need the endpoint_id and a query; the
    knowledge base and hyperparameters are already locked in.
    """
    try:
        return endpoint_service.invoke_endpoint(endpoint_id, request.query)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))