"""Pydantic models for the role-based access control configuration.

The document parsed into these models is `src/data/permissions.v1.json`;
`loader.py` loads and validates it.
"""

from typing import Literal

from pydantic import BaseModel


class RoleConfig(BaseModel):
    """One role a client can act as, with the permissions it grants."""

    role: str
    label: str
    permissions: list[str] = []


class PermissionConfig(BaseModel):
    """A named permission and its human-readable description."""

    description: str


class AuditConfig(BaseModel):
    """Audit logging switches for the authorization layer."""

    log_every_individual_presence_access: bool


class AuthorizationConfig(BaseModel):
    """The permissions.v1.json document: permissions, roles and default policy.

    `default` decides when a role does not grant a permission; the shipped
    file sets it to "deny".
    """

    version: str
    source: str
    default: Literal["deny"]
    audit: AuditConfig
    permissions: dict[str, PermissionConfig]
    roles: list[RoleConfig]

    def get_role(self, role_name: str) -> RoleConfig | None:
        """Return the role named `role_name`, or None when no role has it."""
        return next((role for role in self.roles if role.role == role_name), None)
