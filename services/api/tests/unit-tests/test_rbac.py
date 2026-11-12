"""Tests for the RBAC loader, the permission matrix and mock-token users."""

import pytest
from fastapi import HTTPException

from src.authorization.loader import load_authorization_config
from src.authorization.service import enumerate_permissions, has_permission
from src.security.current_user import User, get_current_user


@pytest.fixture
def config():
    return load_authorization_config()


def test_permission_file_loads_with_all_roles(config):
    assert config.default == "deny"
    assert config.audit.log_every_individual_presence_access is True
    assert {role.role for role in config.roles} == {
        "steward",
        "steward_supervisor",
        "control_room_operator",
        "operations_administrator",
        "it_administrator",
    }


def test_grants_flatten_to_permission_strings(config):
    permissions = enumerate_permissions(config)
    assert permissions["steward"] == {
        "presence.own.all_lines.current_shift",
        "coverage.all.own_lines.current_shift",
    }
    assert permissions["it_administrator"] == {"reference.all.all_lines.all_shifts"}


def test_steward_may_write_own_presence_but_not_others(config):
    steward = User(user_id="u1", role="steward")
    assert has_permission(steward, "presence.own.all_lines.current_shift", config)
    assert not has_permission(steward, "presence.all.own_lines.current_shift", config)
    assert not has_permission(steward, "reference.all.all_lines.all_shifts", config)


def test_broader_grant_covers_narrower_requirement(config):
    operator = User(user_id="u3", role="control_room_operator")
    assert has_permission(operator, "presence.own.all_lines.current_shift", config)
    assert has_permission(operator, "presence.all.all_lines.current_shift", config)
    assert not has_permission(operator, "presence.all.all_lines.all_shifts", config)


def test_supervisor_covers_own_lines_only(config):
    supervisor = User(user_id="u2", role="steward_supervisor")
    assert has_permission(supervisor, "presence.all.own_lines.current_shift", config)
    assert has_permission(supervisor, "presence.own.own_lines.current_shift", config)
    assert not has_permission(
        supervisor, "presence.own.all_lines.current_shift", config
    )


def test_unknown_role_and_malformed_permission_are_denied(config):
    stranger = User(user_id="x", role="no_such_role")
    steward = User(user_id="u1", role="steward")
    assert not has_permission(stranger, "presence.own.all_lines.current_shift", config)
    assert not has_permission(steward, "presence.own", config)
    assert not has_permission(steward, "presence.own.all_lines.someday", config)


def test_get_current_user_defaults_to_dev_steward():
    user = get_current_user()
    assert user.user_id == "user-001"
    assert user.role == "steward"


def test_get_current_user_reads_bearer_token():
    user = get_current_user("Bearer dev-supervisor-token")
    assert user.user_id == "user-002"
    assert user.role == "steward_supervisor"


def test_get_current_user_rejects_unknown_or_malformed_token():
    with pytest.raises(HTTPException) as unknown:
        get_current_user("Bearer nope")
    assert unknown.value.status_code == 401
    with pytest.raises(HTTPException) as malformed:
        get_current_user("Token dev-steward-token")
    assert malformed.value.status_code == 401
