"""Resolve the current user from a request's bearer token and device id.

Dev only: the frontends send the bare role claim as the bearer token and the
device id in `X-Android-Id` (consensus: android_id == user, a 1:1 personal
device). With a real identity-provider token, validation and claim mapping
happen in this module instead.
"""

from uuid import UUID

from fastapi import HTTPException, Request


class User:
    """The authenticated caller: user id, role and personal device id."""

    def __init__(self, user_id: str, role: str, android_id: UUID | None = None):
        self.user_id = user_id
        self.role = role
        self.android_id = android_id


def get_current_user(request: Request) -> User:
    """Return the current user from the `Authorization` and `X-Android-Id` headers.

    The bearer token doubles as user id and role for now (dev only, see the
    module docstring). Raises 401 when the Authorization header is missing or
    not `Bearer <token>`, when the token is empty, or when `X-Android-Id` is
    present but not a valid UUID.
    """
    authorization = request.headers.get("Authorization")
    if authorization is None or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing 'Bearer <token>' header")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty bearer token")
    android_id = request.headers.get("X-Android-Id")
    if android_id is not None:
        try:
            android_id = UUID(android_id)
        except ValueError:
            raise HTTPException(
                status_code=401, detail="Invalid X-Android-Id header"
            ) from None
    return User(user_id=token, role=token, android_id=android_id)
