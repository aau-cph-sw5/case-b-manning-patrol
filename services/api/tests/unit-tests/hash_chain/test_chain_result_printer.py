"""Unit tests for the lines ``verify-chain`` prints per chain."""

import pytest

from src.db.models.integrity_chain_link import ChainName
from src.scripts.verify_chain import ChainResultPrinter


def test_empty_chain_is_not_reported_as_ok(capsys: pytest.CaptureFixture) -> None:
    ChainResultPrinter.print_empty(ChainName.EVENTS)

    assert capsys.readouterr().out == "events: empty (nothing to verify)\n"


@pytest.mark.parametrize(
    ("count", "line"),
    [
        (1, "adjustments: 1 entry has no chain link\n"),
        (3, "adjustments: 3 entries have no chain link\n"),
    ],
)
def test_unlinked_entries_are_reported(
    capsys: pytest.CaptureFixture, count: int, line: str
) -> None:
    ChainResultPrinter.print_unlinked(ChainName.ADJUSTMENTS, count)

    assert capsys.readouterr().out == line
