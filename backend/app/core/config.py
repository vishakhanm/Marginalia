"""
Centralized application configuration.

All services read settings from here via the `get_settings()` singleton
rather than reading environment variables directly. This keeps config
in one place and makes it easy to override in tests.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App metadata ---
    app_name: str = "LLM Playground"
    environment: str = "development"
    debug: bool = True

    # --- API server ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- Ollama ---
    ollama_host: str = "http://localhost:11434"
    default_model: str = "llama3.2"
    default_embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768 

    # --- Qdrant ---
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_prefix: str = "kb_"

    # --- MongoDB ---
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "llm_playground"

    # --- RAG / hyperparameter defaults ---
    default_temperature: float = 0.7
    default_top_k: int = 5
    default_chunk_size: int = 500
    default_chunk_overlap: int = 50
    default_preamble: str = (
        "You are a helpful assistant. Answer the question using only the "
        "provided context. Cite sources where relevant."
    )

     # --- Auth ---
    # IMPORTANT: override this in .env for any non-local deployment.
    jwt_secret_key: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours
 
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
 
    # Where to redirect the browser after a successful OAuth login
    frontend_url: str = "http://localhost:5173"
 
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — import and call this, don't instantiate Settings() directly."""
    return Settings()