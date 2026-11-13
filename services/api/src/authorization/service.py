from src.authorization.models import AuthorizationConfig
from src.security.current_user import User


def has_permission(
    user: User,
    permission: str,
    config: AuthorizationConfig
) -> bool:

    role = config.roles.get(user.role)

    if role is None:
        return False

    if permission not in config.permissions:
        return False

    return permission in role.permissions