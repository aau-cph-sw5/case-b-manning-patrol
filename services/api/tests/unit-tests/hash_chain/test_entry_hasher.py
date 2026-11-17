import pytest

from src.services.hash_chain.entry_hasher import EntryHasher, HashedEntry

TEXT = (
    '{"beacon_id":"550e8400-e29b-41d4-a716-000000000002",'
    '"device_timestamp":"2026-05-30T03:00:00+00:00",'
    '"event_id":"10000000-0000-0000-0000-000000000001",'
    '"event_type":"connect",'
    '"kind":"event",'
    '"server_timestamp":"2026-05-30T03:00:05+00:00",'
    '"source":"test",'
    '"steward_ref":"660e8400-e29b-41d4-a716-446655440001","v":1}'
)
"""Same as GOLDEN_EVENT in test_entry_stringifier.py."""
OTHER_PREV_HASH = "f" * 64

GOLDEN_CONTENT_HASH = "6eeedb567186bf91e8314ee4592e05ea77c0ca2b95f2655ef8d49c81e8d7aa8e"
"""sha256 of TEXT."""
GOLDEN_HEAD_HASH = "063fcaa1d6b74b09291bd223b2df9753573da4a398c91752a5afe7a05291d401"
"""sha256 of GENESIS_HASH followed by GOLDEN_CONTENT_HASH."""
GOLDEN_HEAD_HASH_AFTER_F = (
    "d232f9f888cc2111c0101bff218d495de02e3836fff86c9998fc13b0e9b7df69"
)
"""sha256 of OTHER_PREV_HASH ("f" * 64) followed by GOLDEN_CONTENT_HASH."""


def test_content_hash_matches_the_golden_content_hash():
    hashed = EntryHasher.hash_text(TEXT, EntryHasher.GENESIS_HASH)

    assert hashed.content_hash == GOLDEN_CONTENT_HASH


def test_relinked_text_matches_the_golden_head_hash():
    hashed = EntryHasher.hash_text(TEXT, OTHER_PREV_HASH)

    assert hashed.prev_hash == OTHER_PREV_HASH
    assert hashed.head_hash == GOLDEN_HEAD_HASH_AFTER_F


def test_first_entry_matches_the_golden_head_hash():
    assert (
        EntryHasher.hash_text(TEXT, EntryHasher.GENESIS_HASH).head_hash
        == GOLDEN_HEAD_HASH
    )


def test_same_input_gives_the_same_hashes():
    first = EntryHasher.hash_text(TEXT, EntryHasher.GENESIS_HASH)
    second = EntryHasher.hash_text(TEXT, EntryHasher.GENESIS_HASH)

    assert first == second


def test_changing_the_text_changes_content_and_head_hash():
    original = EntryHasher.hash_text(TEXT, EntryHasher.GENESIS_HASH)
    tampered = EntryHasher.hash_text(
        TEXT.replace("test", "tampered"), EntryHasher.GENESIS_HASH
    )

    assert tampered.content_hash != original.content_hash
    assert tampered.head_hash != original.head_hash


def test_changing_prev_hash_changes_only_the_head_hash():
    original = EntryHasher.hash_text(TEXT, EntryHasher.GENESIS_HASH)
    relinked = EntryHasher.hash_text(TEXT, OTHER_PREV_HASH)

    assert relinked.content_hash == original.content_hash
    assert relinked.head_hash != original.head_hash


def test_hashes_are_64_lowercase_hex_characters():
    hashed: HashedEntry = EntryHasher.hash_text(TEXT, EntryHasher.GENESIS_HASH)

    for value in (hashed.content_hash, hashed.prev_hash, hashed.head_hash):
        assert len(value) == 64
        assert value == value.lower()
        int(value, 16)


@pytest.mark.parametrize("prev_hash", ["", "abc", "F" * 64, "g" * 64])
def test_malformed_prev_hash_is_rejected(prev_hash: str):
    with pytest.raises(ValueError, match="prev_hash"):
        EntryHasher.hash_text(TEXT, prev_hash)
