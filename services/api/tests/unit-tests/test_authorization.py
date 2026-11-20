"""Tests for the RBAC loader, permission file and has_permission matrix."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError


from src.authorization.models import AuthorizationConfig
from src.authorization.authorization_service import AuthorizationService
from src.security.current_user import User


@pytest.fixture
def mock_auth():
    auth_service = Mock(spec=AuthorizationService)
    


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


def test_validate_permissions_raises_on_undefined_permission():
    data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    data["roles"][0]["permissions"].append("does_not_exist")
    config = AuthorizationConfig.model_validate(data)
    with pytest.raises(ValueError, match="does_not_exist"):
        validate_permissions(config)


def test_get_role_returns_none_for_unknown_role(config):
    assert config.get_role("no-such-role") is None


@pytest.mark.parametrize(
    ("role", "permission", "expected"),
    [
        ("steward", "connection_event_send", True),
        ("steward", "disconnection_event_send", True),
        ("steward", "steward_own_patrol_record_view", True),
        ("steward", "station_manning_coverage_view", True),
        ("steward", "patrol_session_start", True),
        ("steward", "train_manning_coverage_view", False),
        ("steward", "adjustment_event_send", False),
        ("steward", "at_risk_count_view", False),
        ("steward", "at_risk_threshold_view", False),
        ("steward", "at_risk_threshold_set", False),
        ("steward", "patrol_record_view_all", False),
        ("stewardSupervisor", "patrol_record_view_all", True),
        ("stewardSupervisor", "train_manning_coverage_view", False),
        ("controlRoomOperator", "train_manning_coverage_view", True),
        ("controlRoomOperator", "adjustment_event_send", True),
        ("controlRoomOperator", "at_risk_count_view", True),
        ("controlRoomOperator", "at_risk_threshold_view", True),
        ("controlRoomOperator", "at_risk_threshold_set", True),
        ("operations_administrator", "patrol_record_view_all", True),
        ("operations_administrator", "at_risk_threshold_set", True),
        ("it_administrator", "connection_event_send", False),
        ("it_administrator", "steward_own_patrol_record_view", False),
        ("unknown-role", "connection_event_send", False),
        ("steward", "not_a_registered_permission", False),
    ],
)
def test_has_permission_matrix(config, role, permission, expected):
    user = User(user_id="u1", role=role)
    assert has_permission(user, permission, config) is expected
