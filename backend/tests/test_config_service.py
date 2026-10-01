from unittest.mock import MagicMock, patch

from app.services import config_service
from app.schemas.hyperparameters import HyperparameterSettings


@patch("app.services.config_service.get_mongo_db")
def test_get_global_config_no_overrides(mock_get_db):
    mock_db = MagicMock()
    mock_db.app_config.find_one.return_value = None
    mock_get_db.return_value = mock_db

    config = config_service.get_global_config()

    assert config.temperature == config_service.settings.default_temperature
    assert config.model == config_service.settings.default_model


@patch("app.services.config_service.get_mongo_db")
def test_get_global_config_with_stored_override(mock_get_db):
    mock_db = MagicMock()
    mock_db.app_config.find_one.return_value = {"_id": "global", "temperature": 0.2}
    mock_get_db.return_value = mock_db

    config = config_service.get_global_config()

    assert config.temperature == 0.2
    # unset fields still fall back to static defaults
    assert config.model == config_service.settings.default_model


@patch("app.services.config_service.get_mongo_db")
def test_update_global_config_only_sets_provided_fields(mock_get_db):
    mock_db = MagicMock()
    mock_db.app_config.find_one.return_value = {"_id": "global", "temperature": 0.9}
    mock_get_db.return_value = mock_db

    updates = HyperparameterSettings(top_k=10)
    config_service.update_global_config(updates)

    mock_db.app_config.update_one.assert_called_once()
    call_args = mock_db.app_config.update_one.call_args
    assert call_args[0][1]["$set"] == {"top_k": 10}


@patch("app.services.config_service.get_mongo_db")
def test_resolve_hyperparameters_priority_order(mock_get_db):
    mock_db = MagicMock()
    mock_db.app_config.find_one.return_value = {"_id": "global", "temperature": 0.5, "top_k": 5}
    mock_get_db.return_value = mock_db

    kb_override = {"temperature": 0.3, "top_k": 8}
    request_override = HyperparameterSettings(temperature=0.1)  # only temperature set

    result = config_service.resolve_hyperparameters(
        request_override=request_override, kb_override=kb_override
    )

    # request override wins for temperature
    assert result.temperature == 0.1
    # kb override wins for top_k since request didn't set it
    assert result.top_k == 8