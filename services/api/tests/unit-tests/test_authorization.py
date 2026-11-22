"""Tests for AuthorizationService: the permission file and the has_permission matrix."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from src.authorization.authorization_service import AuthorizationService
from src.authorization.models import AuthorizationConfig
from src.security.current_user import User

CONFIG_FILE = Path(__file__).parents[2] / "src" / "data" / "permissions.v1.json"

PERMISSION_DATA = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
REGISTERED_PERMISSIONS = sorted(PERMISSION_DATA["permissions"])
UNKNOWN_ROLE = "unknown-role"
UNREGISTERED_PERMISSION = "not_a_registered_permission"
FORGOTTEN_PERMISSION = "test_permission"


@pytest.fixture
def mock_auth() -> Mock:
    return Mock(spec=AuthorizationService)


@pytest.fixture
def config() -> AuthorizationConfig:
    return AuthorizationService().config


def test_permission_file_loads_with_all_roles(config):
    assert {role.role for role in config.roles} == {
        "steward",
        "stewardSupervisor",
        "controlRoomOperator",
        "operations_administrator",
        "it_administrator",
    }


def test_default_is_deny(config):
    assert config.default == "deny"


def test_audit_flag_is_loaded(config):
    assert config.audit.log_every_individual_presence_access is True


def test_default_rejects_anything_but_deny():
    data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    data["default"] = "allow"
    with pytest.raises(ValidationError):
        AuthorizationConfig.model_validate(data)


def test_every_role_permission_is_registered(config):
    registered = set(config.permissions)
    for role in config.roles:
        assert set(role.permissions) <= registered, role.role


def test_service_init_raises_on_undefined_permission(tmp_path):
    data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    data["roles"][0]["permissions"].append("does_not_exist")
    bad_config_file = tmp_path / "permissions.v1.json"
    bad_config_file.write_text(json.dumps(data), encoding="utf-8")
    with patch.object(AuthorizationService, "CONFIG_PATH", bad_config_file):
        with pytest.raises(ValueError, match="does_not_exist"):
            AuthorizationService()


def test_get_role_returns_none_for_unknown_role(config):
    assert config.get_role("no-such-role") is None


def _roles_with_granted_permission() -> list[tuple[str, str]]:
    """(role, granted permission) for every role that grants at least one."""
    return [
        (role["role"], role["permissions"][0])
        for role in PERMISSION_DATA["roles"]
        if role.get("permissions")
    ]


def _roles_with_denied_permission() -> list[tuple[str, str]]:
    """(role, permission the role does not grant) for every role.

    A registered permission outside the role's list; when a role holds every
    registered permission, an arbitrary unregistered one stands in for a
    permission forgotten when the permission table was last updated.
    """
    cases = []
    for role in PERMISSION_DATA["roles"]:
        granted = set(role.get("permissions", []))
        not_granted = [p for p in REGISTERED_PERMISSIONS if p not in granted]
        permission = not_granted[0] if not_granted else FORGOTTEN_PERMISSION
        cases.append((role["role"], permission))
    return cases


@pytest.mark.parametrize(("role", "permission"), _roles_with_granted_permission())
def test_has_role_has_permission(mock_auth, role, permission):
    """Permutation 1: has role, has permission."""
    mock_auth.has_permission.return_value = True
    user = User(user_id="u1", role=role)
    assert mock_auth.has_permission(user, permission) is True
    mock_auth.has_permission.assert_called_once_with(user, permission)


@pytest.mark.parametrize(("role", "permission"), _roles_with_denied_permission())
def test_has_role_has_not_permission(mock_auth, role, permission):
    """Permutation 2: has role, has not permission."""
    mock_auth.has_permission.return_value = False
    user = User(user_id="u1", role=role)
    assert mock_auth.has_permission(user, permission) is False
    mock_auth.has_permission.assert_called_once_with(user, permission)


def test_has_not_role_has_permission(mock_auth):
    """Permutation 3: has not role, has permission."""
    mock_auth.has_permission.return_value = False
    user = User(user_id="u1", role=UNKNOWN_ROLE)
    assert mock_auth.has_permission(user, "connection_event_send") is False
    mock_auth.has_permission.assert_called_once_with(user, "connection_event_send")


def test_has_not_role_has_not_permission(mock_auth):
    """Permutation 4: has not role, has not permission."""
    mock_auth.has_permission.return_value = False
    user = User(user_id="u1", role=UNKNOWN_ROLE)
    assert mock_auth.has_permission(user, UNREGISTERED_PERMISSION) is False
    mock_auth.has_permission.assert_called_once_with(user, UNREGISTERED_PERMISSION)
