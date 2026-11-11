"""Tests for the integrity hash chain classes."""

import datetime
from uuid import UUID

from src.domain.event import EventType
from src.services.hash_chain import HashChain, Sha256Hasher


def test_same_fields_give_same_hash() -> None:
    hasher = Sha256Hasher()
    assert hasher.hash_fields("a", 1) == hasher.hash_fields("a", 1)


def test_argument_boundaries_change_the_hash() -> None:
    hasher = Sha256Hasher()
    assert hasher.hash_fields("ab", "c") != hasher.hash_fields("a", "bc")


def test_field_order_changes_the_hash() -> None:
    hasher = Sha256Hasher()
    assert hasher.hash_fields("a", "b") != hasher.hash_fields("b", "a")


def test_types_are_hashed_in_canonical_form() -> None:
    hasher = Sha256Hasher()
    moment = datetime.datetime(2026, 11, 5, 12, 0, tzinfo=datetime.UTC)
    device = UUID(int=1)
    assert hasher.hash_fields(moment, device, EventType.CONNECT_EVENT, None) == (
        hasher.hash_fields("2026-11-05T12:00:00+00:00", str(device), "connect", None)
    )


def test_chain_links_build_on_each_other() -> None:
    chain = HashChain("events")
    genesis = chain.head_hash
    first = chain.append("a")
    second = chain.append("b")
    assert first.chain == "events"
    assert first.prev_hash == genesis
    assert second.prev_hash == first.head_hash
    assert chain.head_hash == second.head_hash
    assert first.content_hash != second.content_hash


def test_chain_names_keep_chains_separate() -> None:
    events = HashChain("events")
    adjustments = HashChain("adjustments")
    assert events.head_hash != adjustments.head_hash
    assert events.append("x").head_hash != adjustments.append("x").head_hash


class _StubHasher:
    """Hasher stub proving chains depend only on the Hasher protocol."""

    def hash_fields(self, *fields: object) -> str:
        return "|".join(str(field) for field in fields)


def test_chain_accepts_any_hasher_implementation() -> None:
    chain = HashChain("events", hasher=_StubHasher())
    link = chain.append("a")
    assert link.prev_hash == "events"
    assert link.content_hash == "a"
    assert link.head_hash == "events|a"
