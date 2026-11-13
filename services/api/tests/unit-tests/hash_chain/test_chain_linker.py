from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.db.models.adjustment import Adjustment
from src.db.models.event import Event
from src.domain.event import EventRecord, EventType
from src.services.hash_chain.chain_linker import ChainLinker
from src.services.hash_chain.entry_hasher import GENESIS_HASH, EntryHasher
from src.services.hash_chain.entry_stringifier import EntryStringifier
from src.services.shared.event_record_mapper import EventRecordMapper

EVENT_ID = UUID("10000000-0000-0000-0000-000000000001")
ADJUSTMENT_ID = UUID("20000000-0000-0000-0000-000000000001")
STEWARD = UUID("660e8400-e29b-41d4-a716-446655440001")
BEACON = UUID("550e8400-e29b-41d4-a716-000000000002")
DEVICE_AT = datetime(2026, 5, 30, 3, 0, tzinfo=UTC)
SERVER_AT = datetime(2026, 5, 30, 3, 0, 5, tzinfo=UTC)
CORRECTED_AT = datetime(2026, 5, 30, 3, 10, tzinfo=UTC)

GOLDEN_CONTENT_HASH = "c6fabbf488b9a9bc5826dab2b88c7083bd2aab7accbefa34cbb3702071621ee6"
"""Content hash of make_event(); same as in test_entry_hasher.py."""
GOLDEN_HEAD_HASH = "23d96ff06016161032a1777d37ef10893849f45aadc451364df21cad7c34f44e"
"""Head hash of make_event() linked onto GENESIS_HASH."""


def make_event(source: str = "test") -> Event:
    return Event(
        event_id=EVENT_ID,
        event_type=EventType.CONNECT_EVENT,
        android_id=STEWARD,
        beacon_id=BEACON,
        device_timestamp=DEVICE_AT,
        server_timestamp=SERVER_AT,
        source=source,
    )


def make_adjustment() -> Adjustment:
    return Adjustment(
        adjustment_id=ADJUSTMENT_ID,
        target_event_id=EVENT_ID,
        android_id=STEWARD,
        reason="missed stop",
        author="supervisor",
        server_timestamp=SERVER_AT,
        source="test",
        corrected_fact_type=EventType.STOP_EVENT,
        corrected_beacon_id=None,
        corrected_occured_at=CORRECTED_AT,
    )


def test_event_matches_the_golden_hashes():
    linked = ChainLinker.link(make_event(), GENESIS_HASH)

    assert linked.content_hash == GOLDEN_CONTENT_HASH
    assert linked.head_hash == GOLDEN_HEAD_HASH


def test_link_hashes_the_stringified_entry():
    adjustment = make_adjustment()
    text = EntryStringifier.stringify_entry(adjustment)

    linked = ChainLinker.link(adjustment, GENESIS_HASH)

    assert linked == EntryHasher.hash_text(text, GENESIS_HASH)


def test_same_input_gives_the_same_link():
    assert ChainLinker.link(make_event(), GENESIS_HASH) == ChainLinker.link(
        make_event(), GENESIS_HASH
    )


def test_changing_a_field_changes_the_hashes():
    original = ChainLinker.link(make_event(), GENESIS_HASH)
    tampered = ChainLinker.link(make_event(source="tampered"), GENESIS_HASH)

    assert tampered.content_hash != original.content_hash
    assert tampered.head_hash != original.head_hash


def test_domain_event_record_is_rejected():
    record: EventRecord = EventRecordMapper.to_record(make_event())

    with pytest.raises(TypeError, match="EventRecord"):
        ChainLinker.link(record, GENESIS_HASH)  # ty: ignore[invalid-argument-type]


def test_malformed_prev_hash_is_rejected():
    with pytest.raises(ValueError, match="prev_hash"):
        ChainLinker.link(make_event(), "abc")
