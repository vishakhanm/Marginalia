"""
Text chunking — splits long text into overlapping word-based chunks.

Overlap exists so that a sentence or idea that straddles a chunk boundary
isn't split cleanly in half; each new chunk repeats a bit of the previous
one for continuity of meaning during retrieval.
"""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into chunks of `chunk_size` words, with `overlap` words
    repeated between consecutive chunks.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
        start += step

    return chunks