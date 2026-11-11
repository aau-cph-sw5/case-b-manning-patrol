"""Canonical hashing and named hash chains for append-only integrity."""

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Protocol
from uuid import UUID


class Canonicalizer(Protocol):
    """Converts values to a JSON-serializable canonical form."""

    def canonicalize(self, value: object) -> Any:
        """Return the canonical form of one value."""
        ...


class JsonCanonicalizer:
    """Canonicalize values as ISO strings, plain scalars and sorted maps."""

    def canonicalize(self, value: object) -> Any:
        """Convert a value to a JSON-serializable canonical form.

        Datetimes and dates become ISO-8601 strings, UUIDs and enums their
        string value, bytes their hex form, and mappings keep string keys
        so the result is stable regardless of insertion order.
        """
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, Enum):
            return self.canonicalize(value.value)
        if isinstance(value, bytes):
            return value.hex()
        if isinstance(value, dict):
            return {str(key): self.canonicalize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set, frozenset)):
            return [self.canonicalize(item) for item in value]
        return str(value)


class Hasher(Protocol):
    """Hashes any number of fields into one hex digest."""

    def hash_fields(self, *fields: object) -> str:
        """Return the hex digest of the fields, respecting argument boundaries."""
        ...


class Sha256Hasher:
    """SHA-256 hasher over the JSON array of canonicalized fields.

    Depends only on a ``Canonicalizer``, so the serialization rules can be
    swapped without touching the digest logic.
    """

    def __init__(self, canonicalizer: Canonicalizer | None = None) -> None:
        self._canonicalizer: Canonicalizer = canonicalizer or JsonCanonicalizer()

    def hash_fields(self, *fields: object) -> str:
        """Return the SHA-256 hex digest of any number of fields.

        The digest is computed over the JSON array of the canonicalized
        fields, so it depends on argument boundaries:
        ``hash_fields("ab", "c")`` differs from ``hash_fields("a", "bc")``.
        """
        payload = json.dumps(
            [self._canonicalizer.canonicalize(field) for field in fields],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ChainLink:
    """One link appended to a hash chain.

    ``prev_hash`` is the head before the append, ``content_hash`` the
    digest of the appended fields alone and ``head_hash`` the new chain
    head; these are the values an integrity table stores per row.
    """

    chain: str
    prev_hash: str
    content_hash: str
    head_hash: str


class HashChain:
    """A named append-only hash chain holding the current head hash.

    Each chain starts at a genesis head derived from its name, so chains
    with different names never share digests. Depends only on a ``Hasher``;
    the default is SHA-256, but any ``Hasher`` implementation can be
    injected.
    """

    def __init__(self, name: str, hasher: Hasher | None = None) -> None:
        self._name = name
        self._hasher: Hasher = hasher or Sha256Hasher()
        self._head = self._hasher.hash_fields(name)

    @property
    def name(self) -> str:
        """Return the chain name."""
        return self._name

    @property
    def head_hash(self) -> str:
        """Return the current head hash, or the genesis hash before any append."""
        return self._head

    def append(self, *fields: object) -> ChainLink:
        """Link fields onto the chain and return the new link.

        The content hash covers only ``fields``; the new head binds it to
        the previous head, so editing, deleting or reordering any earlier
        link changes every later head.
        """
        content_hash = self._hasher.hash_fields(*fields)
        head_hash = self._hasher.hash_fields(self._head, content_hash)
        link = ChainLink(
            chain=self._name,
            prev_hash=self._head,
            content_hash=content_hash,
            head_hash=head_hash,
        )
        self._head = head_hash
        return link
