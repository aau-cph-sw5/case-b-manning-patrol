from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from src.db.models.event import Event
from src.db.models.integrity_chain_link import ChainName, IntegrityChainLink
from src.domain.event import EventType
from src.services.hash_chain.chain_verifier import (
    ChainBreakReason,
    ChainVerifier,
    LinkedEntry,
)
from src.services.hash_chain.entry_hasher import EntryHasher
from src.services.hash_chain.entry_stringifier import EntryStringifier

STEWARD = UUID("660e8400-e29b-41d4-a716-446655440001")
BEACON = UUID("550e8400-e29b-41d4-a716-000000000002")
DEVICE_AT = datetime(2026, 5, 30, 3, 0, tzinfo=UTC)
SERVER_AT = datetime(2026, 5, 30, 3, 0, 5, tzinfo=UTC)


def make_event() -> Event:
    return Event(
        event_id=uuid4(),
        event_type=EventType.CONNECT_EVENT,
        android_id=STEWARD,
        beacon_id=BEACON,
        device_timestamp=DEVICE_AT,
        server_timestamp=SERVER_AT,
        source="test",
    )


def make_chain(length: int) -> list[LinkedEntry]:
    """Build a valid chain of ``length`` entries with seq 1..length."""
    chain: list[LinkedEntry] = []
    prev_hash = EntryHasher.GENESIS_HASH
    for seq in range(1, length + 1):
        event = make_event()
        entry_text = EntryStringifier.stringify_entry(event)
        hashed = EntryHasher.hash_text(entry_text, prev_hash)
        link = IntegrityChainLink(
            chain=ChainName.EVENTS,
            seq=seq,
            record_id=event.event_id,
            prev_hash=hashed.prev_hash,
            content_hash=hashed.content_hash,
            head_hash=hashed.head_hash,
            server_timestamp=SERVER_AT,
        )
        chain.append(LinkedEntry(link=link, entry=event))
        prev_hash = hashed.head_hash
    return chain


def tamper_with_entry(linked: LinkedEntry) -> None:
    """Change a field of the stored entry after its hashes were recorded."""
    assert linked.entry is not None
    linked.entry.source = "tampered"


def change_entry(chain: list[LinkedEntry]) -> None:
    """Change the second entry after its hashes were recorded."""
    tamper_with_entry(chain[1])


def remove_link(chain: list[LinkedEntry]) -> None:
    """Drop the second link, so the third no longer points at its predecessor."""
    del chain[1]


def edit_head_hash(chain: list[LinkedEntry]) -> None:
    """Overwrite the stored head hash of the second link."""
    chain[1].link.head_hash = "f" * 64


def drop_entry(chain: list[LinkedEntry]) -> None:
    """Keep the second link but lose the entry it points to."""
    chain[1] = LinkedEntry(link=chain[1].link, entry=None)


def change_two_entries(chain: list[LinkedEntry]) -> None:
    """Change the second and third entries after their hashes were recorded."""
    tamper_with_entry(chain[1])
    tamper_with_entry(chain[2])


def test_intact_chain_has_no_break():
    chain = make_chain(3)

    assert ChainVerifier.verify(chain) is None


def test_empty_chain_has_no_break():
    assert ChainVerifier.verify([]) is None


@pytest.mark.parametrize(
    ("damage", "seq", "reason"),
    [
        pytest.param(
            change_entry, 2, ChainBreakReason.CONTENT_MISMATCH, id="entry-changed"
        ),
        pytest.param(remove_link, 3, ChainBreakReason.PREV_MISMATCH, id="link-removed"),
        pytest.param(
            edit_head_hash, 2, ChainBreakReason.HEAD_MISMATCH, id="head-hash-edited"
        ),
        pytest.param(drop_entry, 2, ChainBreakReason.ENTRY_MISSING, id="entry-missing"),
        pytest.param(
            change_two_entries,
            2,
            ChainBreakReason.CONTENT_MISMATCH,
            id="two-entries-changed-reports-first",
        ),
    ],
)
def test_damaged_chain_reports_its_first_break(
    damage: Callable[[list[LinkedEntry]], None],
    seq: int,
    reason: ChainBreakReason,
):
    chain = make_chain(3)
    damage(chain)

    result = ChainVerifier.verify(chain)

    assert result is not None
    assert result.link.seq == seq
    assert result.reason == reason
