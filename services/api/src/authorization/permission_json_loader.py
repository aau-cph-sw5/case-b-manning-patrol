"""Load and validate the RBAC configuration from `data/permissions.v1.json`.

`dependencies.py` loads it once at import time, so a broken file fails at
startup instead of on the first request.
"""

from pathlib import Path

from src.authorization.permission_json_validator import validate_permissions

from .models import AuthorizationConfig

CONFIG_PATH = Path(__file__).parent.parent / "data" / "permissions.v1.json"


def load_authorization_config() -> AuthorizationConfig:
    """Read permissions.v1.json and return it validated.

    Raises ValueError when a role references an undefined permission.
    """
    json_data = CONFIG_PATH.read_text(encoding="utf-8")
    config = AuthorizationConfig.model_validate_json(json_data)

    validate_permissions(config=config)

    return config


