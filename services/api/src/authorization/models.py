from pydantic import BaseModel

class RoleConfig(BaseModel):
    roles
    permissions: list[str]

