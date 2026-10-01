"""
RAG service — retrieval-augmented generation over a knowledge base.

Split into three stages on purpose:
- retrieve_chunks: embed the query, search Qdrant for relevant chunks
- build_prompt: assemble retrieved chunks + preamble into a single prompt
- generate_answer: orchestrates both stages, then calls Ollama for the final answer

Keeping these separate means retrieval or prompt assembly can be tested
or reused (e.g. by the endpoint publisher in a later step) without
needing to also trigger a live model call.
"""

from app.core.db import get_qdrant_client, get_ollama_client
from app.core.config import get_settings
from app.services.embedding_service import embed_text
from app.services.kb_service import _qdrant_collection_name, get_knowledge_base
from app.services.config_service import resolve_hyperparameters
from app.schemas.rag import Citation, ChatResponse
from app.schemas.hyperparameters import HyperparameterSettings

settings = get_settings()

SNIPPET_MAX_CHARS = 300


def retrieve_chunks(kb_id: str, query: str, top_k: int) -> list[dict]:
    """
    Embed the query and search the knowledge base's Qdrant collection
    for the most relevant chunks. Returns raw payload + score dicts.
    """
    qdrant = get_qdrant_client()
    query_vector = embed_text(query)

    results = qdrant.search(
        collection_name=_qdrant_collection_name(kb_id),
        query_vector=query_vector,
        limit=top_k,
    )

    return [
        {
            "document_id": r.payload.get("document_id"),
            "filename": r.payload.get("filename"),
            "chunk_index": r.payload.get("chunk_index"),
            "text": r.payload.get("text", ""),
            "score": r.score,
        }
        for r in results
    ]


def build_prompt(query: str, chunks: list[dict], preamble: str) -> str:
    """
    Assemble retrieved chunks into a single prompt with numbered sources,
    so the model can ground its answer and reference sources by number.
    """
    if not chunks:
        context_block = "No relevant context was found in the knowledge base."
    else:
        context_block = "\n\n".join(
            f"[Source {i + 1}: {c['filename']}, chunk {c['chunk_index']}]\n{c['text']}"
            for i, c in enumerate(chunks)
        )

    return (
        f"{preamble}\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question: {query}\n\n"
        f"Answer using the context above. Reference sources by their number "
        f"(e.g. 'Source 1') where relevant."
    )


def generate_answer(
    kb_id: str,
    query: str,
    model: str | None = None,
    temperature: float | None = None,
    top_k: int | None = None,
    preamble: str | None = None,
) -> ChatResponse:
    """Full RAG pipeline: retrieve -> build prompt -> generate -> return with citations."""
    kb = get_knowledge_base(kb_id)
    if kb is None:
        raise ValueError(f"Knowledge base '{kb_id}' not found")

    request_override = HyperparameterSettings(
        model=model, temperature=temperature, top_k=top_k, preamble=preamble
    )
    kb_override = kb.hyperparameters.model_dump() if kb.hyperparameters else None
    effective = resolve_hyperparameters(request_override=request_override, kb_override=kb_override)

    resolved_model = effective.model
    resolved_temperature = effective.temperature
    resolved_top_k = effective.top_k
    resolved_preamble = effective.preamble

    chunks = retrieve_chunks(kb_id, query, resolved_top_k)
    prompt = build_prompt(query, chunks, resolved_preamble)

    client = get_ollama_client()
    response = client.chat(
        model=resolved_model,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": resolved_temperature},
    )
    answer_text = response["message"]["content"]

    citations = [
        Citation(
            document_id=c["document_id"],
            filename=c["filename"],
            chunk_index=c["chunk_index"],
            text_snippet=(
                c["text"][:SNIPPET_MAX_CHARS] + "..."
                if len(c["text"]) > SNIPPET_MAX_CHARS
                else c["text"]
            ),
            score=c["score"],
        )
        for c in chunks
    ]

    return ChatResponse(
        answer=answer_text,
        citations=citations,
        model=resolved_model,
        kb_id=kb_id,
    )