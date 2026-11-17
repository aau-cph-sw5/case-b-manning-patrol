from typing import Literal

from pydantic import BaseModel


class RoleConfig(BaseModel):
    role: str
    label: str
    permissions: list[str] = []


class PermissionConfig(BaseModel):
    description: str


class AuditConfig(BaseModel):
    log_every_individual_presence_access: bool


class AuthorizationConfig(BaseModel):
    version: str
    source: str
    default: Literal["deny"]
    audit: AuditConfig
    permissions: dict[str, PermissionConfig]
    roles: list[RoleConfig]

    def get_role(self, role_name: str) -> RoleConfig | None:
        return next((role for role in self.roles if role.role == role_name), None)
