

from fastapi import Depends

class User:
    def __init__(self, user_id: str, role: str):
        self.user_id = user_id
        self.role = role


def get_current_user() -> User:
    return User(
        user_id="test-user-001",
        role="patrol_supervisor"
    )