from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.db.models.event import Event
from src.domain.event import EventType
from src.services.hash_chain.entry_hasher import GENESIS_HASH, EntryHasher, HashedEntry

EVENT_ID = UUID("10000000-0000-0000-0000-000000000001")
STEWARD = UUID("660e8400-e29b-41d4-a716-446655440001")
BEACON = UUID("550e8400-e29b-41d4-a716-000000000002")
DEVICE_AT = datetime(2026, 5, 30, 3, 0, tzinfo=UTC)
SERVER_AT = datetime(2026, 5, 30, 3, 0, 5, tzinfo=UTC)
OTHER_PREV_HASH = "f" * 64

GOLDEN_CONTENT_HASH = "c6fabbf488b9a9bc5826dab2b88c7083bd2aab7accbefa34cbb3702071621ee6"
"""sha256 of GOLDEN_EVENT from test_entry_stringifier.py."""
GOLDEN_HEAD_HASH = "23d96ff06016161032a1777d37ef10893849f45aadc451364df21cad7c34f44e"
"""sha256 of GENESIS_HASH followed by GOLDEN_CONTENT_HASH."""
GOLDEN_HEAD_HASH_AFTER_F = (
    "96c40c6591f7f0960244ca958580a93e8a24c291f1d377aea929c312a4667b2b"
)
"""sha256 of OTHER_PREV_HASH ("f" * 64) followed by GOLDEN_CONTENT_HASH."""


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


def test_content_hash_matches_the_golden_content_hash():
    hashed = EntryHasher.hash_entry(make_event(), GENESIS_HASH)

    assert hashed.content_hash == GOLDEN_CONTENT_HASH


def test_relinked_entry_matches_the_golden_head_hash():
    hashed = EntryHasher.hash_entry(make_event(), OTHER_PREV_HASH)

    assert hashed.prev_hash == OTHER_PREV_HASH
    assert hashed.head_hash == GOLDEN_HEAD_HASH_AFTER_F


def test_first_entry_matches_the_golden_head_hash():
    assert (
        EntryHasher.hash_entry(make_event(), GENESIS_HASH).head_hash == GOLDEN_HEAD_HASH
    )


def test_same_input_gives_the_same_hashes():
    first = EntryHasher.hash_entry(make_event(), GENESIS_HASH)
    second = EntryHasher.hash_entry(make_event(), GENESIS_HASH)

    assert first == second


def test_changing_a_field_changes_content_and_head_hash():
    original = EntryHasher.hash_entry(make_event(), GENESIS_HASH)
    tampered = EntryHasher.hash_entry(make_event(source="tampered"), GENESIS_HASH)

    assert tampered.content_hash != original.content_hash
    assert tampered.head_hash != original.head_hash


def test_changing_prev_hash_changes_only_the_head_hash():
    original = EntryHasher.hash_entry(make_event(), GENESIS_HASH)
    relinked = EntryHasher.hash_entry(make_event(), OTHER_PREV_HASH)

    assert relinked.content_hash == original.content_hash
    assert relinked.head_hash != original.head_hash


def test_hashes_are_64_lowercase_hex_characters():
    hashed: HashedEntry = EntryHasher.hash_entry(make_event(), GENESIS_HASH)

    for value in (hashed.content_hash, hashed.prev_hash, hashed.head_hash):
        assert len(value) == 64
        assert value == value.lower()
        int(value, 16)


@pytest.mark.parametrize("prev_hash", ["", "abc", "F" * 64, "g" * 64])
def test_malformed_prev_hash_is_rejected(prev_hash: str):
    with pytest.raises(ValueError, match="prev_hash"):
        EntryHasher.hash_entry(make_event(), prev_hash)
