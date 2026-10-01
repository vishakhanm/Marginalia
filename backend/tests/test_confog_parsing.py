import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_settings_defaults():
    """With no .env and no environment overrides, class defaults should apply."""
    s = Settings(_env_file=None)
    assert s.app_name == "LLM Playground"
    assert s.default_model == "llama3.2"
    assert s.default_embedding_model == "nomic-embed-text"
    assert s.embedding_dim == 768
    assert s.qdrant_host == "localhost"
    assert s.qdrant_port == 6333
    assert s.mongo_uri == "mongodb://localhost:27017"
    assert s.default_temperature == 0.7
    assert s.default_top_k == 5
    assert s.default_chunk_size == 500
    assert s.default_chunk_overlap == 50


def test_settings_environment_override(monkeypatch):
    """Environment variables should override class defaults."""
    monkeypatch.setenv("DEFAULT_MODEL", "mistral")
    monkeypatch.setenv("QDRANT_PORT", "9999")
    monkeypatch.setenv("DEFAULT_TEMPERATURE", "0.2")

    s = Settings(_env_file=None)

    assert s.default_model == "mistral"
    assert s.qdrant_port == 9999
    assert s.default_temperature == 0.2


def test_settings_invalid_type_raises():
    """A value that can't be coerced to the field's type should raise a validation error."""
    with pytest.raises(ValidationError):
        Settings(_env_file=None, qdrant_port="not-a-port")


def test_settings_unknown_env_vars_are_ignored(monkeypatch):
    """extra='ignore' means unrelated environment variables shouldn't break settings loading."""
    monkeypatch.setenv("SOME_UNRELATED_VAR", "whatever")
    s = Settings(_env_file=None)
    assert s.app_name == "LLM Playground"  # loaded fine despite the unrelated var


def test_get_settings_is_cached():
    """get_settings() should return the same instance on repeated calls (lru_cache)."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2