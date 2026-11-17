from datetime import UTC, datetime
from uuid import UUID, uuid4

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


def test_intact_chain_has_no_break():
    chain = make_chain(3)

    assert ChainVerifier.verify(chain) is None


def test_empty_chain_has_no_break():
    assert ChainVerifier.verify([]) is None


def test_changed_entry_breaks_at_its_link_with_content_mismatch():
    chain = make_chain(3)
    tamper_with_entry(chain[1])

    result = ChainVerifier.verify(chain)

    assert result is not None
    assert result.link.seq == 2
    assert result.reason == ChainBreakReason.CONTENT_MISMATCH


def test_removed_link_breaks_at_the_next_link_with_prev_mismatch():
    chain = make_chain(3)
    del chain[1]

    result = ChainVerifier.verify(chain)

    assert result is not None
    assert result.link.seq == 3
    assert result.reason == ChainBreakReason.PREV_MISMATCH


def test_edited_head_hash_breaks_at_its_link_with_head_mismatch():
    chain = make_chain(3)
    chain[1].link.head_hash = "f" * 64

    result = ChainVerifier.verify(chain)

    assert result is not None
    assert result.link.seq == 2
    assert result.reason == ChainBreakReason.HEAD_MISMATCH


def test_missing_entry_breaks_at_its_link_with_entry_missing():
    chain = make_chain(3)
    chain[1] = LinkedEntry(link=chain[1].link, entry=None)

    result = ChainVerifier.verify(chain)

    assert result is not None
    assert result.link.seq == 2
    assert result.reason == ChainBreakReason.ENTRY_MISSING


def test_two_changed_entries_report_only_the_first_break():
    chain = make_chain(3)
    tamper_with_entry(chain[1])
    tamper_with_entry(chain[2])

    result = ChainVerifier.verify(chain)

    assert result is not None
    assert result.link.seq == 2
    assert result.reason == ChainBreakReason.CONTENT_MISMATCH
