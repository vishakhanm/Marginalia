from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import pytest

from app.services import rag_service


def _fake_search_result(document_id, filename, chunk_index, text, score):
    r = MagicMock()
    r.payload = {
        "document_id": document_id,
        "filename": filename,
        "chunk_index": chunk_index,
        "text": text,
    }
    r.score = score
    return r


@patch("app.services.rag_service.embed_text")
@patch("app.services.rag_service.get_qdrant_client")
def test_retrieve_chunks(mock_get_qdrant, mock_embed_text):
    mock_embed_text.return_value = [0.1, 0.2, 0.3]
    mock_qdrant = MagicMock()
    mock_qdrant.search.return_value = [
        _fake_search_result("doc-1", "notes.txt", 0, "some relevant text", 0.92)
    ]
    mock_get_qdrant.return_value = mock_qdrant

    results = rag_service.retrieve_chunks("kb-1", "what is X?", top_k=5)

    assert len(results) == 1
    assert results[0]["filename"] == "notes.txt"
    assert results[0]["score"] == 0.92
    mock_qdrant.search.assert_called_once()


def test_build_prompt_with_chunks():
    chunks = [
        {"filename": "notes.txt", "chunk_index": 0, "text": "Paris is the capital of France."}
    ]
    prompt = rag_service.build_prompt("What is the capital of France?", chunks, "Be helpful.")

    assert "Source 1: notes.txt" in prompt
    assert "Paris is the capital of France." in prompt
    assert "What is the capital of France?" in prompt


def test_build_prompt_no_chunks():
    prompt = rag_service.build_prompt("random question", [], "Be helpful.")
    assert "No relevant context was found" in prompt


@patch("app.services.rag_service.get_ollama_client")
@patch("app.services.rag_service.retrieve_chunks")
@patch("app.services.rag_service.get_knowledge_base")
def test_generate_answer_success(mock_get_kb, mock_retrieve, mock_get_ollama):
    mock_get_kb.return_value = MagicMock(id="kb-1", name="Test KB")
    mock_retrieve.return_value = [
        {
            "document_id": "doc-1",
            "filename": "notes.txt",
            "chunk_index": 0,
            "text": "Paris is the capital of France.",
            "score": 0.95,
        }
    ]
    mock_ollama = MagicMock()
    mock_ollama.chat.return_value = {"message": {"content": "The capital of France is Paris (Source 1)."}}
    mock_get_ollama.return_value = mock_ollama

    result = rag_service.generate_answer(kb_id="kb-1", query="What is the capital of France?")

    assert "Paris" in result.answer
    assert len(result.citations) == 1
    assert result.citations[0].filename == "notes.txt"
    assert result.kb_id == "kb-1"


@patch("app.services.rag_service.get_knowledge_base")
def test_generate_answer_kb_not_found(mock_get_kb):
    mock_get_kb.return_value = None
    with pytest.raises(ValueError, match="not found"):
        rag_service.generate_answer(kb_id="missing-kb", query="anything")