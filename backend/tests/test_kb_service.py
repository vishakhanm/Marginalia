from unittest.mock import MagicMock, patch
import pytest

from app.services import kb_service


@patch("app.services.kb_service.get_qdrant_client")
@patch("app.services.kb_service.get_mongo_db")
def test_create_knowledge_base(mock_get_db, mock_get_qdrant):
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    mock_qdrant = MagicMock()
    mock_get_qdrant.return_value = mock_qdrant

    result = kb_service.create_knowledge_base("My KB", "test description")

    assert result.name == "My KB"
    assert result.description == "test description"
    assert result.document_count == 0
    mock_qdrant.create_collection.assert_called_once()
    mock_db.knowledge_bases.insert_one.assert_called_once()


@patch("app.services.kb_service.get_mongo_db")
def test_get_knowledge_base_not_found(mock_get_db):
    mock_db = MagicMock()
    mock_db.knowledge_bases.find_one.return_value = None
    mock_get_db.return_value = mock_db

    result = kb_service.get_knowledge_base("nonexistent-id")
    assert result is None


@patch("app.services.kb_service.embed_batch")
@patch("app.services.kb_service.get_qdrant_client")
@patch("app.services.kb_service.get_mongo_db")
def test_ingest_document_success(mock_get_db, mock_get_qdrant, mock_embed_batch):
    mock_db = MagicMock()
    mock_db.knowledge_bases.find_one.return_value = {
        "_id": "kb-1",
        "name": "Test KB",
        "description": None,
        "created_at": "2025-01-01T00:00:00Z",
        "document_count": 0,
        "chunk_count": 0,
    }
    mock_get_db.return_value = mock_db

    mock_qdrant = MagicMock()
    mock_get_qdrant.return_value = mock_qdrant

    mock_embed_batch.return_value = [[0.1] * 768]  # one chunk -> one vector

    result = kb_service.ingest_document("kb-1", "notes.txt", b"some short document text")

    assert result.status == "success"
    assert result.chunks_created == 1
    mock_qdrant.upsert.assert_called_once()
    mock_db.documents.insert_one.assert_called_once()
    mock_db.knowledge_bases.update_one.assert_called_once()


@patch("app.services.kb_service.get_mongo_db")
def test_ingest_document_kb_not_found(mock_get_db):
    mock_db = MagicMock()
    mock_db.knowledge_bases.find_one.return_value = None
    mock_get_db.return_value = mock_db

    with pytest.raises(ValueError, match="not found"):
        kb_service.ingest_document("missing-kb", "notes.txt", b"content")


@patch("app.services.kb_service.get_mongo_db")
def test_ingest_document_empty_file(mock_get_db):
    mock_db = MagicMock()
    mock_db.knowledge_bases.find_one.return_value = {
        "_id": "kb-1",
        "name": "Test KB",
        "description": None,
        "created_at": "2025-01-01T00:00:00Z",
        "document_count": 0,
        "chunk_count": 0,
    }
    mock_get_db.return_value = mock_db

    with pytest.raises(ValueError, match="No extractable text"):
        kb_service.ingest_document("kb-1", "empty.txt", b"   ")