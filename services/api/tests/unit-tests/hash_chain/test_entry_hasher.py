from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.db.models.event import Event
from src.domain.event import EventType
from src.services.hash_chain.entry_hasher import GENESIS_HASH, HashedEntry, hash_entry

EVENT_ID = UUID("10000000-0000-0000-0000-000000000001")
STEWARD = UUID("660e8400-e29b-41d4-a716-446655440001")
BEACON = UUID("550e8400-e29b-41d4-a716-000000000002")
DEVICE_AT = datetime(2026, 5, 30, 3, 0, tzinfo=UTC)
SERVER_AT = datetime(2026, 5, 30, 3, 0, 5, tzinfo=UTC)
OTHER_PREVIOUS_HASH = "f" * 64

GOLDEN_CONTENT_HASH = "c6fabbf488b9a9bc5826dab2b88c7083bd2aab7accbefa34cbb3702071621ee6"
"""sha256 of GOLDEN_EVENT from test_entry_stringifier.py."""
GOLDEN_HEADER_HASH = "23d96ff06016161032a1777d37ef10893849f45aadc451364df21cad7c34f44e"
"""sha256 of GENESIS_HASH followed by GOLDEN_CONTENT_HASH."""
GOLDEN_HEADER_HASH_AFTER_F = (
    "96c40c6591f7f0960244ca958580a93e8a24c291f1d377aea929c312a4667b2b"
)
"""sha256 of OTHER_PREVIOUS_HASH ("f" * 64) followed by GOLDEN_CONTENT_HASH."""


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
    hashed = hash_entry(make_event(), GENESIS_HASH)

    assert hashed.content_hash == GOLDEN_CONTENT_HASH


def test_relinked_entry_matches_the_golden_header_hash():
    hashed = hash_entry(make_event(), OTHER_PREVIOUS_HASH)

    assert hashed.previous_hash == OTHER_PREVIOUS_HASH
    assert hashed.header_hash == GOLDEN_HEADER_HASH_AFTER_F


def test_first_entry_matches_the_golden_header_hash():
    assert hash_entry(make_event(), GENESIS_HASH).header_hash == GOLDEN_HEADER_HASH


def test_same_input_gives_the_same_hashes():
    first = hash_entry(make_event(), GENESIS_HASH)
    second = hash_entry(make_event(), GENESIS_HASH)

    assert first == second


def test_changing_a_field_changes_content_and_header_hash():
    original = hash_entry(make_event(), GENESIS_HASH)
    tampered = hash_entry(make_event(source="tampered"), GENESIS_HASH)

    assert tampered.content_hash != original.content_hash
    assert tampered.header_hash != original.header_hash


def test_changing_previous_hash_changes_only_the_header_hash():
    original = hash_entry(make_event(), GENESIS_HASH)
    relinked = hash_entry(make_event(), OTHER_PREVIOUS_HASH)

    assert relinked.content_hash == original.content_hash
    assert relinked.header_hash != original.header_hash


def test_hashes_are_64_lowercase_hex_characters():
    hashed: HashedEntry = hash_entry(make_event(), GENESIS_HASH)

    for value in (hashed.content_hash, hashed.previous_hash, hashed.header_hash):
        assert len(value) == 64
        assert value == value.lower()
        int(value, 16)


@pytest.mark.parametrize("previous_hash", ["", "abc", "F" * 64, "g" * 64])
def test_malformed_previous_hash_is_rejected(previous_hash: str):
    with pytest.raises(ValueError, match="previous_hash"):
        hash_entry(make_event(), previous_hash)
