from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.schemas.hyperparameters import HyperparameterSettings

class CreateKnowledgeBaseRequest(BaseModel):
    name: str = Field(..., description="Human-readable name for the knowledge base")
    description: Optional[str] = None
    hyperparameters: Optional[HyperparameterSettings] = Field(
        None, description="Optional KB-specific hyperparameter overrides"
    )

class UpdateKnowledgeBaseRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class KnowledgeBaseInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    document_count: int = 0
    chunk_count: int = 0
    hyperparameters: Optional[HyperparameterSettings] = None

class KnowledgeBaseListResponse(BaseModel):
    knowledge_bases: list[KnowledgeBaseInfo]
    count: int

class DocumentInfo(BaseModel):
    id: str
    kb_id: str
    filename: str
    chunk_count: int
    uploaded_at: datetime

class UploadDocumentResponse(BaseModel):
    kb_id: str
    document_id: str
    filename: str
    chunks_created: int
    status: str

class FailedUpload(BaseModel):
    filename: str
    error: str
 
class BatchUploadResponse(BaseModel):
    kb_id: str
    uploaded: list[UploadDocumentResponse]
    failed: list[FailedUpload]
 
class DeleteResponse(BaseModel):
    id: str
    status: str