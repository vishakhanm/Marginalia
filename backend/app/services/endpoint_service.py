"""
Endpoint publishing service — saves a {name, kb_id, hyperparameters} combo
as a reusable "published endpoint," and runs inference against it on demand.

This deliberately doesn't duplicate any RAG logic: invoking an endpoint just
calls rag_service.generate_answer with the endpoint's saved kb_id and
hyperparameters as the request-level override, so it slots into the same
priority chain built in Step 6 (endpoint config > KB profile > global > static).
"""

import uuid
from datetime import datetime, timezone

from app.core.db import get_mongo_db
from app.schemas.endpoint import EndpointInfo, EndpointListResponse, DeleteEndpointResponse
from app.schemas.hyperparameters import HyperparameterSettings
from app.schemas.rag import ChatResponse


def _doc_to_info(doc: dict) -> EndpointInfo:
    fields = {k: v for k, v in doc.items() if k != "_id"}
    if fields.get("hyperparameters"):
        fields["hyperparameters"] = HyperparameterSettings(**fields["hyperparameters"])
    return EndpointInfo(id=doc["_id"], **fields)


def create_endpoint(
    name: str, kb_id: str, hyperparameters: HyperparameterSettings | None
) -> EndpointInfo:
    """Save a new published endpoint config. Does not validate kb_id existence here —
    that's checked at invoke time via generate_answer, keeping this fast and simple."""
    db = get_mongo_db()

    endpoint_id = str(uuid.uuid4())
    doc = {
        "_id": endpoint_id,
        "name": name,
        "kb_id": kb_id,
        "hyperparameters": hyperparameters.model_dump(exclude_none=True) if hyperparameters else None,
        "created_at": datetime.now(timezone.utc),
        "call_count": 0,
        "last_called_at": None,
    }
    db.endpoints.insert_one(doc)
    return _doc_to_info(doc)


def list_endpoints() -> EndpointListResponse:
    db = get_mongo_db()
    endpoints = [_doc_to_info(doc) for doc in db.endpoints.find()]
    return EndpointListResponse(endpoints=endpoints, count=len(endpoints))


def get_endpoint(endpoint_id: str) -> EndpointInfo | None:
    db = get_mongo_db()
    doc = db.endpoints.find_one({"_id": endpoint_id})
    return _doc_to_info(doc) if doc else None


def delete_endpoint(endpoint_id: str) -> DeleteEndpointResponse:
    db = get_mongo_db()
    db.endpoints.delete_one({"_id": endpoint_id})
    return DeleteEndpointResponse(id=endpoint_id, status="success")


def invoke_endpoint(endpoint_id: str, query: str) -> ChatResponse:
    """
    Run RAG using this endpoint's saved kb_id and hyperparameters, then
    record the call for basic usage tracking.
    """
    from app.services import rag_service  # local import avoids a circular import at module load

    db = get_mongo_db()
    endpoint = get_endpoint(endpoint_id)
    if endpoint is None:
        raise ValueError(f"Endpoint '{endpoint_id}' not found")

    hp = endpoint.hyperparameters or HyperparameterSettings()

    result = rag_service.generate_answer(
        kb_id=endpoint.kb_id,
        query=query,
        model=hp.model,
        temperature=hp.temperature,
        top_k=hp.top_k,
        preamble=hp.preamble,
    )

    db.endpoints.update_one(
        {"_id": endpoint_id},
        {"$inc": {"call_count": 1}, "$set": {"last_called_at": datetime.now(timezone.utc)}},
    )

    return result