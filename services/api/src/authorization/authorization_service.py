"""Permission checks of a user's role against the loaded RBAC config."""

from pathlib import Path

from src.authorization.models import AuthorizationConfig
from src.security.current_user import User


class AuthorizationService:
    CONFIG_PATH = Path(__file__).parent.parent / "data" / "permissions.v1.json"

    def __init__(self):
        """Read permissions.v1.json and return it validated.

        Raises ValueError when a role references an undefined permission.
        """
        json_data = self.CONFIG_PATH.read_text(encoding="utf-8")
        self.config = AuthorizationConfig.model_validate_json(json_data)

        self._validate_permissions()

    def _validate_permissions(self) -> None:
        """Raise ValueError if any role references an undefined permission."""
        defined_permissions = set(self.config.permissions)

        for role in self.config.roles:
            for permission in role.permissions:
                if permission not in defined_permissions:
                    raise ValueError(
                        f"Role '{role.role}' references "
                        f"undefined permission '{permission}'"
                    )

    def has_permission(self, user: User, permission: str) -> bool:
        """Return whether the user's role grants `permission`.

        The config's `default` decides when the role does not grant it; the shipped
        permissions.v1.json sets "deny", so unknown permissions are rejected.
        """
        role = self.config.get_role(user.role)

        if role is not None and permission in role.permissions:
            return True
        return self.config.default == "allow"
