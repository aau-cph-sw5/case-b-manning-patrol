from fastapi import Depends

class User:
    def __init__(self, android_id: str, role: str):
        self.user_id = android_id
        self.role = role


def get_current_user() -> User:
    return User(
        user_id = "test_user_01",
        role = "Steward")
