
from src.authorization.models import AuthenticationConfig
from src.security.current_user import User


def has_permission(
        user: User,
        permission: str,
        config: AuthenticationConfig
) -> bool:

    role = config.role.get(user.role)

    if role is None:
        return False

    if permission not in config.permissions:
        return False

    return permission in role.permissions