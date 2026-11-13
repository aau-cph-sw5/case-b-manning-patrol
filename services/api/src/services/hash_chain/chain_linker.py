"""Link a stored event or adjustment onto the hash chain.

Combines ``EntryStringifier`` and ``EntryHasher``: the entry is turned into its
fixed string, which is then hashed and chained onto the previous head hash.
Events and adjustments share one chain. Nothing here reads or writes the
database; the caller passes in the chain's current head hash and stores the
result.
"""

from src.services.hash_chain.entry_hasher import EntryHasher, HashedEntry
from src.services.hash_chain.entry_stringifier import ChainEntry, EntryStringifier


class ChainLinker:
    """Turn a stored entry into its chain hashes, linked onto a previous hash."""

    @staticmethod
    def link(entry: ChainEntry, prev_hash: str) -> HashedEntry:
        """Return the hashes of ``entry`` chained onto ``prev_hash``.

        Pass the chain's current head hash, or ``GENESIS_HASH`` for the first
        entry. Calling again with the same arguments gives the same result, so
        a caller whose save was rejected can re-read the head and link again.

        Raises TypeError for anything other than an ``Event`` or
        ``Adjustment``, and ValueError for a timestamp without a time zone or
        a ``prev_hash`` that is not 64 lowercase hex characters.
        """
        text = EntryStringifier.stringify_entry(entry)
        return EntryHasher.hash_text(text, prev_hash)
