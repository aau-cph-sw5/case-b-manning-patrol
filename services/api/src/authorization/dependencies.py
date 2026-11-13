from fastapi import Depends, HTTPException
from src.authorization.loader import load_authorization_config
from src.authorization.service import has_permission
from src.security.current_user import User, get_current_user

config = load_authorization_config()


def require_permission(permission: str):

    def permission_checker(
        user: User = Depends(get_current_user)
    ) -> User:

        if not has_permission(user, permission, config):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )

        return user

    return permission_checker