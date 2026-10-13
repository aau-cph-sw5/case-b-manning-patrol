import json
from pathlib import Path

import pytest

from src.main import app

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}

CONTRACTS_DIR = Path(__file__).parents[3] / "contracts"


PUBLISHED_CONTRACTS = [
    CONTRACTS_DIR / "api" / "v2" / "positioning-ingestion" / "schema.json",
]


def _contract_routes(schema_path: Path) -> set[tuple[str, str]]:
    schema = json.loads(schema_path.read_text())
    routes = set()
    for raw_path, methods in schema["paths"].items():
        path = raw_path if raw_path.startswith("/") else f"/{raw_path}"
        for method in methods:
            routes.add((method.upper(), path))
    return routes


def _app_routes() -> set[tuple[str, str]]:
    schema = app.openapi()
    routes = set()
    for path, operations in schema["paths"].items():
        for method in operations:
            if method.upper() in HTTP_METHODS:
                routes.add((method.upper(), path))
    return routes


@pytest.mark.parametrize(
    "schema_path",
    PUBLISHED_CONTRACTS,
    ids=lambda p: f"{p.parent.parent.name}/{p.parent.name}",
)
def test_contract_routes_are_served(schema_path: Path):
    missing = _contract_routes(schema_path) - _app_routes()
    assert not missing, (
        f"{schema_path} documents routes the app doesn't serve: {missing}"
    )
