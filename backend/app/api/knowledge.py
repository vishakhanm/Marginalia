from fastapi import APIRouter, HTTPException, UploadFile, File

from app.schemas.knowledge import (
    CreateKnowledgeBaseRequest, UpdateKnowledgeBaseRequest, KnowledgeBaseInfo,
    KnowledgeBaseListResponse, BatchUploadResponse, DeleteResponse,
)
from app.services import kb_service
from app.schemas.hyperparameters import HyperparameterSettings

router = APIRouter()


@router.post("", response_model=KnowledgeBaseInfo)
def create_knowledge_base(request: CreateKnowledgeBaseRequest):
    """Create a new, empty knowledge base."""
    return kb_service.create_knowledge_base(
        request.name, request.description, request.hyperparameters
    )


@router.get("", response_model=KnowledgeBaseListResponse)
def list_knowledge_bases():
    """List all knowledge bases."""
    return kb_service.list_knowledge_bases()


@router.get("/{kb_id}", response_model=KnowledgeBaseInfo)
def get_knowledge_base(kb_id: str):
    """Fetch details for a single knowledge base."""
    kb = kb_service.get_knowledge_base(kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_id}' not found")
    return kb

@router.patch("/{kb_id}", response_model=KnowledgeBaseInfo)
def update_knowledge_base(kb_id: str, request: UpdateKnowledgeBaseRequest):
    """Rename and/or redescribe a knowledge base."""
    kb = kb_service.update_knowledge_base_details(kb_id, request.name, request.description)
    if kb is None:
        raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_id}' not found")
    return kb

@router.patch("/{kb_id}/hyperparameters", response_model=KnowledgeBaseInfo)
def update_hyperparameters(kb_id: str, hyperparameters: HyperparameterSettings):
    """Set or update this knowledge base's hyperparameter profile (partial updates supported)."""
    kb = kb_service.update_knowledge_base_hyperparameters(kb_id, hyperparameters)
    if kb is None:
        raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_id}' not found")
    return kb


@router.delete("/{kb_id}", response_model=DeleteResponse)
def delete_knowledge_base(kb_id: str):
    """Delete a knowledge base, its documents, and its vectors."""
    return kb_service.delete_knowledge_base(kb_id)


@router.post("/{kb_id}/upload", response_model=BatchUploadResponse)
async def upload_documents(kb_id: str, files: list[UploadFile] = File(...)):
    """Upload and ingest one or more documents (PDF/DOCX/TXT/CSV/XLSX) into a knowledge base."""
    file_data = []
    for f in files:
        content = await f.read()
        file_data.append((f.filename, content))
    try:
        return kb_service.ingest_documents(kb_id, file_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))