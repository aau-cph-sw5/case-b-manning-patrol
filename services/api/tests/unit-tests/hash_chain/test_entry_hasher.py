import hashlib
from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.db.models.event import Event
from src.domain.event import EventType
from src.services.hash_chain.entry_hasher import GENESIS_HASH, HashedEntry, hash_entry
from src.services.hash_chain.entry_stringifier import stringify

EVENT_ID = UUID("10000000-0000-0000-0000-000000000001")
STEWARD = UUID("660e8400-e29b-41d4-a716-446655440001")
BEACON = UUID("550e8400-e29b-41d4-a716-000000000002")
DEVICE_AT = datetime(2026, 5, 30, 3, 0, tzinfo=UTC)
SERVER_AT = datetime(2026, 5, 30, 3, 0, 5, tzinfo=UTC)
OTHER_PREVIOUS_HASH = "f" * 64

GOLDEN_HEADER_HASH = "a1bb40026efaf5b528b61680141aa43996ba13ade649986d944cdd417ba22589"


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


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_content_hash_is_the_hash_of_the_stringified_entry():
    hashed = hash_entry(make_event(), GENESIS_HASH)

    assert hashed.content_hash == sha256(stringify(make_event()))


def test_header_hash_covers_previous_hash_then_content_hash():
    hashed = hash_entry(make_event(), OTHER_PREVIOUS_HASH)

    assert hashed.previous_hash == OTHER_PREVIOUS_HASH
    assert hashed.header_hash == sha256(OTHER_PREVIOUS_HASH + hashed.content_hash)


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
