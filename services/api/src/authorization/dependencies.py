"""FastAPI dependencies that guard endpoints with RBAC permissions.

The config is loaded once at import time; see `loader.py`.
"""

from typing import Annotated

from fastapi import Depends, HTTPException

from src.authorization.loader import load_authorization_config
from src.authorization.service import has_permission
from src.security.current_user import User, get_current_user

config = load_authorization_config()


def require_permission(permission: str):
    """Return a dependency that requires `permission` of the current user.

    The returned checker resolves the user from the bearer token, raises 403
    when the user's role does not grant the permission, and returns the user
    when it does.
    """

    def permission_checker(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:

        if not has_permission(user, permission, config):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return user

    return permission_checker
