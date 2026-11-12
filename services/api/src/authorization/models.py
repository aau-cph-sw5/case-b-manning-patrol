"""Pydantic models mirroring the permission file src/data/permissions.v1.json."""

from typing import Literal

from pydantic import BaseModel

DataKind = Literal["presence", "coverage", "reference"]
Scope = Literal["own", "all"]
ShiftScope = Literal["current", "all"]

SUBJECT_TOKENS = {"own": "own", "all": "all"}
LINES_TOKENS = {"own": "own_lines", "all": "all_lines"}
SHIFT_TOKENS = {"current": "current_shift", "all": "all_shifts"}


class Grant(BaseModel):
    """One cell of the role x permission matrix: data, subject, lines, shift."""

    data: DataKind
    subject: Scope
    lines: Scope
    shift_scope: ShiftScope

    def as_permission(self) -> str:
        """Flatten to a readable permission string.

        Example: data=presence, subject=own, lines=all, shift_scope=current
        becomes 'presence.own.all_lines.current_shift'.
        """
        return (
            f"{self.data}.{SUBJECT_TOKENS[self.subject]}"
            f".{LINES_TOKENS[self.lines]}.{SHIFT_TOKENS[self.shift_scope]}"
        )


class RoleConfig(BaseModel):
    """A role and the compound grants it holds."""

    role: str
    label: str
    grants: list[Grant]

    def permissions(self) -> set[str]:
        """Return the role's grants as flattened permission strings."""
        return {grant.as_permission() for grant in self.grants}


class AuditConfig(BaseModel):
    """Audit switches from the permission file."""

    log_every_individual_presence_access: bool


class AuthorizationConfig(BaseModel):
    """The whole permission file: default policy, audit flags and roles."""

    version: str
    source: str
    default: Literal["allow", "deny"]
    audit: AuditConfig
    roles: list[RoleConfig]

    def get_role(self, name: str) -> RoleConfig | None:
        """Return the role with this name, or None when it is not defined."""
        return next((role for role in self.roles if role.role == name), None)
