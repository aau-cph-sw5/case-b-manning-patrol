"""Load and validate the RBAC permission file (src/data/permissions.v1.json)."""

import json
from functools import lru_cache
from pathlib import Path

from .models import AuthorizationConfig

CONFIG_PATH = Path(__file__).parent.parent / "data" / "permissions.v1.json"


@lru_cache(maxsize=1)
def load_authorization_config() -> AuthorizationConfig:
    """Read and validate the permission file once per process."""
    with CONFIG_PATH.open(encoding="utf-8") as file:
        data = json.load(file)
    config = AuthorizationConfig.model_validate(data)
    validate_config(config)
    return config


def validate_config(config: AuthorizationConfig) -> None:
    """Reject duplicate role names and roles without grants."""
    seen: set[str] = set()
    for role in config.roles:
        if role.role in seen:
            raise ValueError(f"Duplicate role '{role.role}' in {CONFIG_PATH.name}")
        if not role.grants:
            raise ValueError(f"Role '{role.role}' in {CONFIG_PATH.name} has no grants")
        seen.add(role.role)
