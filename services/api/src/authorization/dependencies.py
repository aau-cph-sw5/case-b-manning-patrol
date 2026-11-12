"""FastAPI dependencies for authentication and RBAC permission checks."""

from typing import Annotated

from fastapi import Depends, HTTPException

from src.authorization.loader import load_authorization_config
from src.authorization.models import AuthorizationConfig
from src.authorization.service import has_permission
from src.security.current_user import User, get_current_user


def get_authorization_config() -> AuthorizationConfig:
    """Return the cached permission config (override this in tests if needed)."""
    return load_authorization_config()


AuthorizationConfigDep = Annotated[
    AuthorizationConfig, Depends(get_authorization_config)
]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_permission(permission: str):
    """Build a dependency demanding a flattened permission string.

    The permission is a readable dot-joined grant, e.g.
    'presence.own.all_lines.current_shift'. Raises 403 when the caller's
    role does not cover it under the file's default policy.
    """

    def permission_checker(
        user: CurrentUserDep, config: AuthorizationConfigDep
    ) -> User:
        if not has_permission(user, permission, config):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return permission_checker
