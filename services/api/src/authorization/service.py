from src.authorization.models import AuthorizationConfig
from src.security.current_user import User


def has_permission(user: User, permission: str, config: AuthorizationConfig) -> bool:

    role = config.get_role(user.role)

    if role is not None and permission in role.permissions:
        return True
    return config.default == "allow"
