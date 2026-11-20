"""FastAPI dependencies that guard endpoints with RBAC permissions.

The config is loaded once at import time; see `loader.py`.
"""

from typing import Annotated

from fastapi import Depends, HTTPException

from src.authorization.authorization_service import AuthorizationService
from src.security.current_user import User, get_current_user


def require_permission(permission: str):
    """Return a dependency that requires `permission` of the current user.

    The returned checker resolves the user from the bearer token, raises 403
    when the user's role does not grant the permission, and returns the user
    when it does.
    """

    def permission_checker(
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:

        auth_service = AuthorizationService()

        if not auth_service.has_permission(user, permission):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return user

    return permission_checker
