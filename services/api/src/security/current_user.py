from uuid import UUID

from fastapi import HTTPException, Request


class User:
    def __init__(self, user_id: str, role: str, android_id: UUID | None = None):
        self.user_id = user_id
        self.role = role
        self.android_id = android_id


def get_current_user(request: Request) -> User:
    authorization = request.headers.get("Authorization")
    if authorization is None or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing 'Bearer <token>' header")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty bearer token")
    # Dev only: the frontends send the bare role claim as the bearer token and the
    # device id in X-Android-Id (consensus: android_id == user, 1:1 personal
    # device). With a real Entra ID token, validate it here instead and resolve
    # user_id from "oid", role from "roles"[0], android_id from the oid mapping.
    android_id = request.headers.get("X-Android-Id")
    if android_id is not None:
        try:
            android_id = UUID(android_id)
        except ValueError:
            raise HTTPException(
                status_code=401, detail="Invalid X-Android-Id header"
            ) from None
    return User(user_id=token, role=token, android_id=android_id)
