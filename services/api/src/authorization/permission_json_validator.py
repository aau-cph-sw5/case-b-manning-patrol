from src.authorization.models import AuthorizationConfig


def validate_permissions(config: AuthorizationConfig) -> None:
    """Raise ValueError if any role references an undefined permission."""
    defined_permissions = set(config.permissions)

    for role in config.roles:
        for permission in role.permissions:
            if permission not in defined_permissions:
                raise ValueError(
                    f"Role '{role.role}' references undefined permission '{permission}'"
                )
