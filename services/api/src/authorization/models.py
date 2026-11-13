from pydantic import BaseModel


class RoleConfig(BaseModel):
    role: str
    label: str
    permissions: list[str]


class PermissionConfig(BaseModel):
    description: str


class AuthorizationConfig(BaseModel):
    version: str
    source: str
    default: str
    audit: dict
    permissions: dict[str, PermissionConfig]
    roles: list[RoleConfig]
    
    def get_role(self, role_name: str) -> RoleConfig | None:
        return next(
            (role for role in self.roles if role.role == role_name),
            None
        )