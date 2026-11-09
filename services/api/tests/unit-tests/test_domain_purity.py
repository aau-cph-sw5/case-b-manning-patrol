"""The domain package must not depend on storage, API, or service code."""

import ast
from pathlib import Path

import pytest

DOMAIN_DIR = Path(__file__).parents[2] / "src" / "domain"
FORBIDDEN_PREFIXES = ("sqlmodel", "sqlalchemy", "src.api", "src.db", "src.services")


def imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    modules.extend(
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    return modules


@pytest.mark.parametrize(
    "path", sorted(DOMAIN_DIR.glob("*.py")), ids=lambda path: path.name
)
def test_domain_module_has_no_layer_leakage(path: Path) -> None:
    for module in imported_modules(path):
        assert not module.startswith(FORBIDDEN_PREFIXES), (
            f"{path.name} imports {module}"
        )
