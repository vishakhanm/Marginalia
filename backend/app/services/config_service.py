"""
Config service — manages runtime-tunable global hyperparameter defaults.

Stored as a single document (_id="global") in the `app_config` Mongo
collection. Any field never explicitly set falls back to the static
defaults in core/config.py, so the app always has a complete, valid
set of hyperparameters even right after a fresh install.
"""

from app.core.db import get_mongo_db
from app.core.config import get_settings
from app.schemas.hyperparameters import GlobalConfigResponse, HyperparameterSettings

settings = get_settings()

GLOBAL_CONFIG_ID = "global"


def _static_defaults() -> dict:
    return {
        "model": settings.default_model,
        "temperature": settings.default_temperature,
        "top_k": settings.default_top_k,
        "chunk_size": settings.default_chunk_size,
        "chunk_overlap": settings.default_chunk_overlap,
        "preamble": settings.default_preamble,
    }


def get_global_config() -> GlobalConfigResponse:
    """Return the effective global config: stored overrides merged over static defaults."""
    db = get_mongo_db()
    stored = db.app_config.find_one({"_id": GLOBAL_CONFIG_ID}) or {}
    merged = {**_static_defaults(), **{k: v for k, v in stored.items() if k != "_id" and v is not None}}
    return GlobalConfigResponse(**merged)


def update_global_config(updates: HyperparameterSettings) -> GlobalConfigResponse:
    """Persist only the fields that were actually provided; leave the rest untouched."""
    db = get_mongo_db()
    fields_to_set = {k: v for k, v in updates.model_dump().items() if v is not None}

    if fields_to_set:
        db.app_config.update_one(
            {"_id": GLOBAL_CONFIG_ID},
            {"$set": fields_to_set},
            upsert=True,
        )

    return get_global_config()


def resolve_hyperparameters(
    request_override: HyperparameterSettings | None = None,
    kb_override: dict | None = None,
) -> GlobalConfigResponse:
    """
    Resolve the effective hyperparameters using the priority order:
    request override > knowledge-base profile > global runtime config > static defaults.
    """
    effective = get_global_config().model_dump()

    if kb_override:
        effective.update({k: v for k, v in kb_override.items() if v is not None})

    if request_override:
        effective.update(
            {k: v for k, v in request_override.model_dump().items() if v is not None}
        )

    return GlobalConfigResponse(**effective)