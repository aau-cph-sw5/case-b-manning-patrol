"""Resolve the current user from a mock bearer token (development only)."""

from typing import Annotated

from fastapi import Header, HTTPException

from src.security.mock_jwt import DEFAULT_DEV_TOKEN, MOCK_TOKENS


class User:
    """The authenticated caller: a stable user id and one RBAC role name."""

    def __init__(self, user_id: str, role: str):
        self.user_id = user_id
        self.role = role


def get_current_user(authorization: Annotated[str | None, Header()] = None) -> User:
    """Return the user for the Bearer token in the Authorization header.

    Without a header the default dev token is used, so replaying the fixture
    events against `uv run dev` still authenticates as a steward and every
    request is checked against permissions.v1.json. Unknown or malformed
    tokens get 401.
    """
    token = DEFAULT_DEV_TOKEN
    if authorization is not None:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() != "bearer" or not value:
            raise HTTPException(status_code=401, detail="Expected 'Bearer <token>'")
        token = value
    claims = MOCK_TOKENS.get(token)
    if claims is None:
        raise HTTPException(status_code=401, detail="Unknown token")
    return User(user_id=claims["object_id"], role=claims["roles"][0])
