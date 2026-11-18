from dataclasses import dataclass


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
