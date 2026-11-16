"""Check stored chain links against the entries they were made from.

Walks the links of one chain oldest first, links each entry again with
``ChainLinker`` and compares the result with what is stored. The first link
that does not match is reported. Nothing here reads or writes the database;
``ChainLoader`` supplies the links and their entries.
"""

from dataclasses import dataclass
from enum import StrEnum

from src.db.models.integrity_chain_link import IntegrityChainLink
from src.services.hash_chain.chain_linker import ChainLinker
from src.services.hash_chain.entry_hasher import GENESIS_HASH
from src.services.hash_chain.entry_stringifier import ChainEntry


@dataclass(frozen=True)
class LinkedEntry:
    """A stored chain link together with the entry it points to.

    ``entry`` is None when the event or adjustment the link points to no
    longer exists.
    """

    link: IntegrityChainLink
    entry: ChainEntry | None


class ChainBreakReason(StrEnum):
    """What was observed at the link where the chain broke.

    Each value reads as the end of "broken at seq N: ". The reasons describe
    the mismatch, not who caused it: a changed entry and an edited stored
    hash look the same.
    """

    ENTRY_MISSING = "the entry this link points to no longer exists"
    PREV_MISMATCH = "the previous hash is not the head hash of the link before"
    CONTENT_MISMATCH = "the entry no longer matches the content hash stored for it"
    HEAD_MISMATCH = "the stored head hash does not match its previous and content hash"


@dataclass(frozen=True)
class ChainBreak:
    """The first link at which a chain failed verification.

    ``link`` carries the chain, ``seq`` and ids needed to point at the
    failing place; ``reason`` says which check failed.
    """

    link: IntegrityChainLink
    reason: ChainBreakReason


class ChainVerifier:
    """Find the first link in a chain that does not match its entry."""

    @staticmethod
    def verify(linked_entries: list[LinkedEntry]) -> ChainBreak | None:
        """Return the first break in the chain, or None if every link holds.

        ``linked_entries`` must be one chain's links ordered oldest first, starting
        at the beginning of the chain. Each link is checked in this order:
        the entry exists, its previous hash is the head hash of the link
        before (``GENESIS_HASH`` for the first), and the entry linked again
        gives the stored content hash and head hash. Stops at the first
        failing check, so later links are not examined. An empty list has no
        break.
        """
        expected_prev = GENESIS_HASH
        for linked_entry in linked_entries:
            link = linked_entry.link
            if linked_entry.entry is None:
                return ChainBreak(link, ChainBreakReason.ENTRY_MISSING)
            if link.prev_hash != expected_prev:
                return ChainBreak(link, ChainBreakReason.PREV_MISMATCH)

            hashed = ChainLinker.link(linked_entry.entry, expected_prev)
            if hashed.content_hash != link.content_hash:
                return ChainBreak(link, ChainBreakReason.CONTENT_MISMATCH)
            if hashed.head_hash != link.head_hash:
                return ChainBreak(link, ChainBreakReason.HEAD_MISMATCH)
            expected_prev = link.head_hash
        return None
