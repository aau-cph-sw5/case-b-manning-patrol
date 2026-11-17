"""Hash a stringified entry and link it to the head hash before it.

Each entry gets three values: a hash of its own content, the head hash of the
previous entry, and a new head hash over both. Because every head hash
includes the one before it, changing or removing an earlier entry changes
every head hash after it. Nothing here is stored; callers decide what to
persist.
"""

import hashlib
import re
from datetime import UTC, datetime

from src.services.hash_chain.hashed_entry import HashedEntry


class EntryHasher:
    GENESIS_HASH = "0" * 64
    """The previous hash of the first entry in a chain, which has no predecessor."""
    _SHA256_HEX = re.compile(r"[0-9a-f]{64}")
    """Hash entry text and link it onto the previous head hash.

    Works on text only and knows nothing about events or adjustments;
    ``ChainLinker`` turns an entry into text first.
    """

    @staticmethod
    def hash_text(text: str, prev_hash: str) -> HashedEntry:
        """Return the hashes of ``text`` chained onto ``prev_hash``.

        Pass ``GENESIS_HASH`` for the first entry. Raises ValueError if
        ``prev_hash`` is not 64 lowercase hex characters, since the head hash
        is only unambiguous when both parts have that fixed length.
        """
        if not EntryHasher._SHA256_HEX.fullmatch(prev_hash):
            raise ValueError("prev_hash must be 64 lowercase hex characters")
        content_hash = EntryHasher._sha256(text)
        head_hash = EntryHasher._sha256(prev_hash + content_hash)
        return HashedEntry(
            content_hash=content_hash,
            prev_hash=prev_hash,
            head_hash=head_hash,
        )

    @staticmethod
    def _sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _now_utc() -> datetime:
        return datetime.now(UTC)
