"""Mock bearer tokens for development, one per RBAC role.

In production these claims come from a real JWT; here each token maps to a
fixed user id and a role name from src/data/permissions.v1.json.
"""

DEFAULT_DEV_TOKEN = "dev-steward-token"

MOCK_TOKENS: dict[str, dict] = {
    "dev-steward-token": {
        "object_id": "user-001",
        "tenant_id": "development-tenant",
        "name": "Test Steward",
        "roles": ["steward"],
    },
    "dev-supervisor-token": {
        "object_id": "user-002",
        "tenant_id": "development-tenant",
        "name": "Test Steward Supervisor",
        "roles": ["steward_supervisor"],
    },
    "dev-control-room-token": {
        "object_id": "user-003",
        "tenant_id": "development-tenant",
        "name": "Test Control Room Operator",
        "roles": ["control_room_operator"],
    },
    "dev-operations-admin-token": {
        "object_id": "user-004",
        "tenant_id": "development-tenant",
        "name": "Test Operations Administrator",
        "roles": ["operations_administrator"],
    },
    "dev-it-admin-token": {
        "object_id": "user-005",
        "tenant_id": "development-tenant",
        "name": "Test IT Administrator",
        "roles": ["it_administrator"],
    },
}
