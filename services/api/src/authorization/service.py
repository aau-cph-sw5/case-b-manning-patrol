"""Permission checks of a user's role against the loaded RBAC config."""

from src.authorization.models import AuthorizationConfig
from src.security.current_user import User


def has_permission(user: User, permission: str, config: AuthorizationConfig) -> bool:
    """Return whether the user's role grants `permission`.

    The config's `default` decides when the role does not grant it; the shipped
    permissions.v1.json sets "deny", so unknown permissions are rejected.
    """
    role = config.get_role(user.role)

    if role is not None and permission in role.permissions:
        return True
    return config.default == "allow"
