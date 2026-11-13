import json
from pathlib import Path

from .models import AuthorizationConfig


CONFIG_PATH = Path(__file__).parent / "config" / "permissions.json"


def load_authorization_config() -> AuthorizationConfig:
    with CONFIG_PATH.open(encoding="utf-8") as file:
        data = json.load(file)

    config = AuthorizationConfig.model_validate(data)

    validate_permissions(config)

    return config


def validate_permissions(config: AuthorizationConfig) -> None:
    defined_permissions = set(config.permissions)

    for role_name, role in config.roles.items():
        for permission in role.permissions:
            if permission not in defined_permissions:
                raise ValueError(
                    f"Role '{role_name}' references undefined "
                    f"permission '{permission}'"
                )