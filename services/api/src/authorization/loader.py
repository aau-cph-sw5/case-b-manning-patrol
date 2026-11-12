import json
from pathlib import Path
from signal import default_int_handler

from .models import AuthenticationConfig

CONFIG_PATH = Path(__file__).parent.parent / "data" / "permissions.v1.json"

def load_authorization_config() -> AuthenticationConfig:
    with CONFIG_PATH.open(encoding="utf-8") as file:
        data = json.load(file)

    config = AuthenticationConfig.model_validate(data)

    validate_permission(config)

    return config

def validate_permission(config: AuthenticationConfig) -> None:
    defined_permissions = set(config.permissions)

    for role_name, role in config.role.items():
        for permission in role.permissions:
            if permission not in defined_permissions:
                raise ValueError(
                    f"Role '{role_name}' references undefined "
                    f"permission '{permission}'"
                )