from fastapi import HTTPException, Request


class User:
    def __init__(self, user_id: str, role: str):
        self.user_id = user_id
        self.role = role


def get_current_user(request: Request) -> User:
    authorization = request.headers.get("Authorization")
    if authorization is None or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing 'Bearer <token>' header")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty bearer token")
    # No sign-in yet: the frontends send the bare role claim as the bearer token
    # (apps/web and apps/android src/api/auth.ts). When a real IdP token arrives,
    # validate it here instead and read user_id from "oid", role from "roles"[0].
    return User(user_id=token, role=token)
