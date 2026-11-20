"""Load and validate the RBAC configuration from `data/permissions.v1.json`.

`dependencies.py` loads it once at import time, so a broken file fails at
startup instead of on the first request.
"""

from pathlib import Path

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


def validate_permissions(config: AuthorizationConfig) -> None:
    """Raise ValueError if any role references an undefined permission."""
    defined_permissions = set(config.permissions)

    for role in config.roles:
        for permission in role.permissions:
            if permission not in defined_permissions:
                raise ValueError(
                    f"Role '{role.role}' references undefined permission '{permission}'"
                )
