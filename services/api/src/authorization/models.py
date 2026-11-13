from pydantic import BaseModel


class RoleConfig(BaseModel):
    description: str
    permissions: list[str]


class PermissionConfig(BaseModel):
    description: str


class AuthorizationConfig(BaseModel):
    roles: dict[str, RoleConfig]
    permissions: dict[str, PermissionConfig]