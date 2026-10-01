"""
Chat history service — persists conversations and messages per user.

A "conversation" is a Mongo document (kb_id, title, timestamps); each
message within it is a separate document referencing the conversation
by id. save_exchange() is the main entry point, called once per /chat
request: it either continues an existing conversation or starts a new
one, then records both the user's question and the assistant's answer.
"""

import uuid
from datetime import datetime, timezone

from app.core.db import get_mongo_db
from app.schemas.history import (
    ConversationInfo,
    ConversationListResponse,
    MessageInfo,
    ConversationDetailResponse,
    DeleteConversationResponse,
)
from app.schemas.rag import ChatResponse, Citation

TITLE_MAX_CHARS = 60


def _conversation_doc_to_info(doc: dict) -> ConversationInfo:
    return ConversationInfo(id=doc["_id"], **{k: v for k, v in doc.items() if k != "_id"})


def _message_doc_to_info(doc: dict) -> MessageInfo:
    fields = {k: v for k, v in doc.items() if k != "_id"}
    if fields.get("citations"):
        fields["citations"] = [Citation(**c) for c in fields["citations"]]
    return MessageInfo(id=doc["_id"], **fields)


def _create_conversation(user_id: str, kb_id: str, title: str) -> ConversationInfo:
    db = get_mongo_db()
    conversation_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    doc = {
        "_id": conversation_id,
        "user_id": user_id,
        "kb_id": kb_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
    }
    db.conversations.insert_one(doc)
    return _conversation_doc_to_info(doc)


def _add_message(
    conversation_id: str, role: str, content: str, citations: list[Citation] | None = None
) -> MessageInfo:
    db = get_mongo_db()
    message_id = str(uuid.uuid4())
    doc = {
        "_id": message_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "citations": [c.model_dump() for c in citations] if citations else None,
        "created_at": datetime.now(timezone.utc),
    }
    db.messages.insert_one(doc)
    return _message_doc_to_info(doc)


def list_conversations(user_id: str) -> ConversationListResponse:
    db = get_mongo_db()
    docs = db.conversations.find({"user_id": user_id}).sort("updated_at", -1)
    conversations = [_conversation_doc_to_info(d) for d in docs]
    return ConversationListResponse(conversations=conversations, count=len(conversations))


def get_conversation(conversation_id: str, user_id: str) -> ConversationDetailResponse | None:
    """Returns None if the conversation doesn't exist OR belongs to a different user —
    callers shouldn't be able to distinguish those two cases (404 either way)."""
    db = get_mongo_db()
    doc = db.conversations.find_one({"_id": conversation_id, "user_id": user_id})
    if doc is None:
        return None

    message_docs = db.messages.find({"conversation_id": conversation_id}).sort("created_at", 1)
    messages = [_message_doc_to_info(m) for m in message_docs]
    return ConversationDetailResponse(conversation=_conversation_doc_to_info(doc), messages=messages)


def delete_conversation(conversation_id: str, user_id: str) -> DeleteConversationResponse:
    db = get_mongo_db()
    db.conversations.delete_one({"_id": conversation_id, "user_id": user_id})
    db.messages.delete_many({"conversation_id": conversation_id})
    return DeleteConversationResponse(id=conversation_id, status="success")


def save_exchange(
    user_id: str,
    kb_id: str,
    conversation_id: str | None,
    query: str,
    response: ChatResponse,
) -> ConversationInfo:
    """
    Record one question/answer exchange. If conversation_id is given and
    belongs to this user, append to it; otherwise start a new conversation
    titled from the query.
    """
    db = get_mongo_db()

    conversation = None
    if conversation_id:
        existing = db.conversations.find_one({"_id": conversation_id, "user_id": user_id})
        if existing:
            conversation = _conversation_doc_to_info(existing)

    if conversation is None:
        title = query if len(query) <= TITLE_MAX_CHARS else query[:TITLE_MAX_CHARS] + "..."
        conversation = _create_conversation(user_id, kb_id, title)

    _add_message(conversation.id, role="user", content=query)
    _add_message(conversation.id, role="assistant", content=response.answer, citations=response.citations)

    db.conversations.update_one(
        {"_id": conversation.id}, {"$set": {"updated_at": datetime.now(timezone.utc)}}
    )

    return conversation