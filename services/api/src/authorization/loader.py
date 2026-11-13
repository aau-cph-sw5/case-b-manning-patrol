from pathlib import Path

from .models import AuthorizationConfig


CONFIG_PATH = Path(__file__).parent / "data" / "permissions.v1.json"


def load_authorization_config() -> AuthorizationConfig:
    json_data = CONFIG_PATH.read_text(encoding="utf-8")
    config = AuthorizationConfig.model_validate_json(json_data)

    validate_permissions(config)

    return config


def validate_permissions(config: AuthorizationConfig) -> None:
    defined_permissions = set(config.permissions)

    for role in config.roles:
        for permission in role.permissions:
            if permission not in defined_permissions:
                raise ValueError(
                    f"Role '{role.role}' references undefined "
                    f"permission '{permission}'"
                )