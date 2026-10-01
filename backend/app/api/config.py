from fastapi import APIRouter

from app.schemas.hyperparameters import GlobalConfigResponse, UpdateGlobalConfigRequest
from app.services import config_service

router = APIRouter()


@router.get("", response_model=GlobalConfigResponse)
def get_config():
    """View the current effective global hyperparameter defaults."""
    return config_service.get_global_config()


@router.put("", response_model=GlobalConfigResponse)
def update_config(request: UpdateGlobalConfigRequest):
    """Update one or more global hyperparameter defaults at runtime (no restart needed)."""
    return config_service.update_global_config(request)