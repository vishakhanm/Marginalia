"""
Knowledge base service — orchestrates the full ingestion pipeline:
parse file -> chunk text -> embed chunks -> store vectors in Qdrant
and metadata in MongoDB.

A "knowledge base" is represented as:
- one MongoDB document in the `knowledge_bases` collection (name, description,
  counts, and optional hyperparameter overrides)
- one Qdrant collection named f"{prefix}{kb_id}" holding all its chunk vectors
- one MongoDB document per uploaded file in the `documents` collection
"""

import uuid
from datetime import datetime, timezone

from qdrant_client.models import VectorParams, Distance, PointStruct

from app.core.db import get_mongo_db, get_qdrant_client
from app.core.config import get_settings
from app.utils.parsers import parse_file
from app.utils.chunking import chunk_text
from app.services.embedding_service import embed_batch
from app.schemas.knowledge import (
    KnowledgeBaseInfo, KnowledgeBaseListResponse, UploadDocumentResponse,
    BatchUploadResponse, FailedUpload, DeleteResponse,
)
from app.schemas.hyperparameters import HyperparameterSettings

settings = get_settings()


def _qdrant_collection_name(kb_id: str) -> str:
    return f"{settings.qdrant_collection_prefix}{kb_id}"


def _doc_to_info(doc: dict) -> KnowledgeBaseInfo:
    fields = {k: v for k, v in doc.items() if k != "_id"}
    if fields.get("hyperparameters"):
        fields["hyperparameters"] = HyperparameterSettings(**fields["hyperparameters"])
    return KnowledgeBaseInfo(id=doc["_id"], **fields)


def create_knowledge_base(
    name: str,
    description: str | None,
    hyperparameters: HyperparameterSettings | None = None,
) -> KnowledgeBaseInfo:
    """Create a new knowledge base: a Mongo record + an empty Qdrant collection."""
    db = get_mongo_db()
    qdrant = get_qdrant_client()

    kb_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)

    qdrant.create_collection(
        collection_name=_qdrant_collection_name(kb_id),
        vectors_config=VectorParams(size=settings.embedding_dim, distance=Distance.COSINE),
    )

    doc = {
        "_id": kb_id,
        "name": name,
        "description": description,
        "created_at": created_at,
        "document_count": 0,
        "chunk_count": 0,
        "hyperparameters": hyperparameters.model_dump(exclude_none=True) if hyperparameters else None,
    }
    db.knowledge_bases.insert_one(doc)

    return _doc_to_info(doc)


def list_knowledge_bases() -> KnowledgeBaseListResponse:
    db = get_mongo_db()
    kbs = [_doc_to_info(doc) for doc in db.knowledge_bases.find()]
    return KnowledgeBaseListResponse(knowledge_bases=kbs, count=len(kbs))


def get_knowledge_base(kb_id: str) -> KnowledgeBaseInfo | None:
    db = get_mongo_db()
    doc = db.knowledge_bases.find_one({"_id": kb_id})
    if not doc:
        return None
    return _doc_to_info(doc)

def update_knowledge_base_details(
    kb_id: str, name: str | None, description: str | None
) -> KnowledgeBaseInfo | None:
    """Rename and/or redescribe a knowledge base. Only provided fields change."""
    db = get_mongo_db()
    existing = db.knowledge_bases.find_one({"_id": kb_id})
    if not existing:
        return None

    updates = {}
    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if updates:
        db.knowledge_bases.update_one({"_id": kb_id}, {"$set": updates})
    return get_knowledge_base(kb_id)


def update_knowledge_base_hyperparameters(
    kb_id: str, hyperparameters: HyperparameterSettings
) -> KnowledgeBaseInfo | None:
    """Set or update this knowledge base's hyperparameter profile."""
    db = get_mongo_db()
    existing = db.knowledge_bases.find_one({"_id": kb_id})
    if not existing:
        return None

    current = existing.get("hyperparameters") or {}
    updates = hyperparameters.model_dump(exclude_none=True)
    merged = {**current, **updates}

    db.knowledge_bases.update_one({"_id": kb_id}, {"$set": {"hyperparameters": merged}})
    return get_knowledge_base(kb_id)


def delete_knowledge_base(kb_id: str) -> DeleteResponse:
    """Delete the Mongo record, its document records, and the Qdrant collection."""
    db = get_mongo_db()
    qdrant = get_qdrant_client()

    db.knowledge_bases.delete_one({"_id": kb_id})
    db.documents.delete_many({"kb_id": kb_id})

    collection_name = _qdrant_collection_name(kb_id)
    if qdrant.collection_exists(collection_name):
        qdrant.delete_collection(collection_name)

    return DeleteResponse(id=kb_id, status="success")


def ingest_document(kb_id: str, filename: str, content: bytes) -> UploadDocumentResponse:
    """
    Full ingestion pipeline for one uploaded file:
    parse -> chunk -> embed -> upsert into Qdrant -> record in Mongo.

    Uses this KB's chunk_size/chunk_overlap override if one is set,
    otherwise falls back to the global config default.
    """
    from app.services.config_service import resolve_hyperparameters

    db = get_mongo_db()
    qdrant = get_qdrant_client()

    kb = get_knowledge_base(kb_id)
    if kb is None:
        raise ValueError(f"Knowledge base '{kb_id}' not found")

    text = parse_file(filename, content)
    if not text.strip():
        raise ValueError(f"No extractable text found in '{filename}'")

    kb_override = kb.hyperparameters.model_dump() if kb.hyperparameters else None
    effective = resolve_hyperparameters(kb_override=kb_override)

    chunks = chunk_text(text, chunk_size=effective.chunk_size, overlap=effective.chunk_overlap)
    if not chunks:
        raise ValueError(f"File '{filename}' produced no chunks")

    vectors = embed_batch(chunks)

    document_id = str(uuid.uuid4())
    collection_name = _qdrant_collection_name(kb_id)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "kb_id": kb_id,
                "document_id": document_id,
                "filename": filename,
                "chunk_index": idx,
                "text": chunk,
            },
        )
        for idx, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]
    qdrant.upsert(collection_name=collection_name, points=points)

    uploaded_at = datetime.now(timezone.utc)
    db.documents.insert_one(
        {
            "_id": document_id,
            "kb_id": kb_id,
            "filename": filename,
            "chunk_count": len(chunks),
            "uploaded_at": uploaded_at,
        }
    )

    db.knowledge_bases.update_one(
        {"_id": kb_id},
        {"$inc": {"document_count": 1, "chunk_count": len(chunks)}},
    )

    return UploadDocumentResponse(
        kb_id=kb_id,
        document_id=document_id,
        filename=filename,
        chunks_created=len(chunks),
        status="success",
    )

def ingest_documents(kb_id: str, files: list[tuple[str, bytes]]) -> BatchUploadResponse:
    """
    Ingest multiple files in one call. The KB's existence is checked once up
    front (raises ValueError -> 404 if missing); per-file problems (bad
    format, empty content) are collected into `failed` instead of aborting
    the whole batch, so one bad file doesn't block the rest.
    """
    kb = get_knowledge_base(kb_id)
    if kb is None:
        raise ValueError(f"Knowledge base '{kb_id}' not found")

    uploaded = []
    failed = []
    for filename, content in files:
        try:
            result = ingest_document(kb_id, filename, content)
            uploaded.append(result)
        except ValueError as e:
            failed.append(FailedUpload(filename=filename, error=str(e)))

    return BatchUploadResponse(kb_id=kb_id, uploaded=uploaded, failed=failed)