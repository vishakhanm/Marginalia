import pytest
from app.utils.chunking import chunk_text


def test_chunk_text_basic():
    text = " ".join(f"word{i}" for i in range(1000))
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    # each chunk should have roughly chunk_size words (last one may be shorter)
    for chunk in chunks[:-1]:
        assert len(chunk.split()) == 100


def test_chunk_text_overlap():
    text = " ".join(f"word{i}" for i in range(100))
    chunks = chunk_text(text, chunk_size=30, overlap=10)
    first_tail = chunks[0].split()[-10:]
    second_head = chunks[1].split()[:10]
    assert first_tail == second_head


def test_chunk_text_empty_string():
    assert chunk_text("", chunk_size=50, overlap=5) == []


def test_chunk_text_shorter_than_chunk_size():
    text = "just a few words here"
    chunks = chunk_text(text, chunk_size=50, overlap=5)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=10, overlap=10)