from unittest.mock import MagicMock, patch
import pytest

from app.services import kb_service


@patch("app.services.kb_service.get_mongo_db")
def test_update_knowledge_base_details_renames(mock_get_db):
    mock_db = MagicMock()
    mock_db.knowledge_bases.find_one.side_effect = [
        {"_id": "kb-1", "name": "Old Name", "description": "Old desc", "created_at": "2025-01-01T00:00:00Z",
         "document_count": 0, "chunk_count": 0, "hyperparameters": None},
        {"_id": "kb-1", "name": "New Name", "description": "Old desc", "created_at": "2025-01-01T00:00:00Z",
         "document_count": 0, "chunk_count": 0, "hyperparameters": None},
    ]
    mock_get_db.return_value = mock_db

    result = kb_service.update_knowledge_base_details("kb-1", name="New Name", description=None)

    assert result.name == "New Name"
    mock_db.knowledge_bases.update_one.assert_called_once_with({"_id": "kb-1"}, {"$set": {"name": "New Name"}})


@patch("app.services.kb_service.get_mongo_db")
def test_update_knowledge_base_details_not_found(mock_get_db):
    mock_db = MagicMock()
    mock_db.knowledge_bases.find_one.return_value = None
    mock_get_db.return_value = mock_db

    result = kb_service.update_knowledge_base_details("missing-kb", name="X", description=None)
    assert result is None


@patch("app.services.kb_service.ingest_document")
@patch("app.services.kb_service.get_knowledge_base")
def test_ingest_documents_mixed_success_and_failure(mock_get_kb, mock_ingest_document):
    mock_get_kb.return_value = MagicMock(id="kb-1")

    def side_effect(kb_id, filename, content):
        if filename == "bad.txt":
            raise ValueError(f"No extractable text found in '{filename}'")
        from app.schemas.knowledge import UploadDocumentResponse
        return UploadDocumentResponse(kb_id=kb_id, document_id="doc-1", filename=filename, chunks_created=3, status="success")

    mock_ingest_document.side_effect = side_effect

    result = kb_service.ingest_documents(
        "kb-1", [("good.txt", b"real content"), ("bad.txt", b"")]
    )

    assert len(result.uploaded) == 1
    assert result.uploaded[0].filename == "good.txt"
    assert len(result.failed) == 1
    assert result.failed[0].filename == "bad.txt"


@patch("app.services.kb_service.get_knowledge_base")
def test_ingest_documents_kb_not_found(mock_get_kb):
    mock_get_kb.return_value = None
    with pytest.raises(ValueError, match="not found"):
        kb_service.ingest_documents("missing-kb", [("a.txt", b"content")])