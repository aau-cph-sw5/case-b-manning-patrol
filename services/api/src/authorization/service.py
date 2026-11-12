"""Grant-based permission checks against the loaded RBAC config."""

from src.authorization.models import (
    LINES_TOKENS,
    SHIFT_TOKENS,
    SUBJECT_TOKENS,
    AuthorizationConfig,
)
from src.security.current_user import User

_DATA_KINDS = {"presence", "coverage", "reference"}
_SCOPE_RANK = {"own": 0, "current": 0, "all": 1}
_SUBJECT_BY_TOKEN = {token: value for value, token in SUBJECT_TOKENS.items()}
_LINES_BY_TOKEN = {token: value for value, token in LINES_TOKENS.items()}
_SHIFT_BY_TOKEN = {token: value for value, token in SHIFT_TOKENS.items()}


def enumerate_permissions(config: AuthorizationConfig) -> dict[str, set[str]]:
    """Flatten every role's grants into readable permission strings.

    Each grant becomes 'data.subject.lines.shift', e.g.
    'presence.own.all_lines.current_shift'.
    """
    return {role.role: role.permissions() for role in config.roles}


def _parse_permission(permission: str) -> tuple[str, str, str, str] | None:
    """Split a permission string into raw scope values, or None if malformed."""
    parts = permission.split(".")
    if len(parts) != 4:
        return None
    data, subject_token, lines_token, shift_token = parts
    subject = _SUBJECT_BY_TOKEN.get(subject_token)
    lines = _LINES_BY_TOKEN.get(lines_token)
    shift = _SHIFT_BY_TOKEN.get(shift_token)
    if data not in _DATA_KINDS or subject is None or lines is None or shift is None:
        return None
    return data, subject, lines, shift


def has_permission(user: User, permission: str, config: AuthorizationConfig) -> bool:
    """Return True when the user's role covers the permission.

    `permission` is a readable grant string like 'presence.own.all_lines.current_shift'.
    A grant covers the requirement when data matches exactly and each scope
    segment is equal or broader ('all' covers 'own', 'all_shifts' covers
    'current_shift'). When no grant matches, the file's "default" policy
    decides (the shipped file is "deny", and unknown roles or malformed
    permissions also fall back to it).
    """
    parsed = _parse_permission(permission)
    if parsed is None:
        return config.default == "allow"
    data, subject, lines, shift_scope = parsed
    role = config.get_role(user.role)
    if role is None:
        return config.default == "allow"
    for grant in role.grants:
        if (
            grant.data == data
            and _SCOPE_RANK[grant.subject] >= _SCOPE_RANK[subject]
            and _SCOPE_RANK[grant.lines] >= _SCOPE_RANK[lines]
            and _SCOPE_RANK[grant.shift_scope] >= _SCOPE_RANK[shift_scope]
        ):
            return True
    return config.default == "allow"
