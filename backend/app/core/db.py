"""
Shared database and vector store client instances.

Services import get_mongo_db() / get_qdrant_client() rather than
constructing their own clients, so there's a single connection pool
per process and consistent config.
"""

from functools import lru_cache

from pymongo import MongoClient
from pymongo.database import Database
from qdrant_client import QdrantClient
from ollama import Client as OllamaClient

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def get_mongo_client() -> MongoClient:
    return MongoClient(settings.mongo_uri)


def get_mongo_db() -> Database:
    client = get_mongo_client()
    return client[settings.mongo_db_name]


@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

@lru_cache
def get_ollama_client() -> OllamaClient:
    return OllamaClient(host=settings.ollama_host)