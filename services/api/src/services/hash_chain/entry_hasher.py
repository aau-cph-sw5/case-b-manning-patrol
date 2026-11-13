"""Hash a stored event or adjustment and link it to the entry before it.

Each entry gets three values: a hash of its own content, the head hash of the
previous entry, and a new head hash over both. Because every head hash
includes the one before it, changing or removing an earlier entry changes
every head hash after it. Nothing here is stored; callers decide what to
persist.
"""

import hashlib
import re
from dataclasses import dataclass

from src.services.hash_chain.entry_stringifier import ChainEntry, EntryStringifier

GENESIS_HASH = "0" * 64
"""The previous hash of the first entry in a chain, which has no predecessor."""

_SHA256_HEX = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class HashedEntry:
    """The hashes of one entry and its link to the previous entry.

    All three are SHA-256 digests as 64 lowercase hex characters.
    ``content_hash`` covers the entry alone, so its content can be checked
    without the rest of the chain. ``prev_hash`` is the ``head_hash`` of the
    entry before it, or ``GENESIS_HASH`` for the first entry. ``head_hash``
    covers ``prev_hash`` followed by ``content_hash``.
    """

    content_hash: str
    prev_hash: str
    head_hash: str


class EntryHasher:
    """Hash chain entries and link each one onto the previous head hash."""

    @staticmethod
    def hash_entry(entry: ChainEntry, prev_hash: str) -> HashedEntry:
        """Return the hashes of ``entry`` chained onto ``prev_hash``.

        Pass ``GENESIS_HASH`` for the first entry. Raises ValueError if
        ``prev_hash`` is not 64 lowercase hex characters, since the head hash
        is only unambiguous when both parts have that fixed length.
        """
        if not _SHA256_HEX.fullmatch(prev_hash):
            raise ValueError("prev_hash must be 64 lowercase hex characters")
        content_hash = EntryHasher._sha256(EntryStringifier.stringify_entry(entry))
        head_hash = EntryHasher._sha256(prev_hash + content_hash)
        return HashedEntry(
            content_hash=content_hash,
            prev_hash=prev_hash,
            head_hash=head_hash,
        )

    @staticmethod
    def _sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
