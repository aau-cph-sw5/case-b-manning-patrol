"""Turn a stored event or adjustment into the fixed string that gets hashed.

The same entry must always give exactly the same string, whenever and wherever
it is stringified: keys are sorted, there is no whitespace, UUIDs are lowercase
strings and every timestamp is written in UTC. Only the fields listed in
``EVENT_FIELDS`` and ``ADJUSTMENT_FIELDS`` are included, and every string is
tagged with ``FORMAT_VERSION``, so the hash format changes only when someone
edits those lists or bumps the version on purpose.
"""

import json
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from src.db.models.adjustment import Adjustment
from src.db.models.event import Event

ChainEntry = Event | Adjustment
"""A stored row that belongs in the chain: an ``Event`` or an ``Adjustment``."""


FORMAT_VERSION = 1
"""Version of the string format, written into every stringified entry as ``"v"``."""

EVENT_FIELDS = (
    "event_id",
    "event_type",
    "android_id",
    "beacon_id",
    "device_timestamp",
    "server_timestamp",
    "source",
)
"""``Event`` columns included in the string; must cover every column."""

ADJUSTMENT_FIELDS = (
    "adjustment_id",
    "target_event_id",
    "android_id",
    "reason",
    "author",
    "server_timestamp",
    "source",
    "corrected_fact_type",
    "corrected_beacon_id",
    "corrected_occured_at",
)
"""``Adjustment`` columns included in the string; must cover every column."""


def stringify(entry: ChainEntry) -> str:
    """Return ``entry`` as a compact JSON string with sorted keys.

    A ``kind`` key ("event" or "adjustment") is added so an event and an
    adjustment can never produce the same string, and a ``"v"`` key carries
    ``FORMAT_VERSION`` so entries hashed under an older format stay
    recognisable. ``None`` becomes ``null``.

    Raises TypeError for anything other than an ``Event`` or ``Adjustment``
    row (API schemas and domain records are not hashed), and ValueError for a
    timestamp without a time zone.
    """
    if isinstance(entry, Event):
        kind, field_names = "event", EVENT_FIELDS
    elif isinstance(entry, Adjustment):
        kind, field_names = "adjustment", ADJUSTMENT_FIELDS
    else:
        raise TypeError(
            f"Cannot stringify {type(entry).__name__}; expected Event or Adjustment",
        )
    fields = {name: _to_json_value(getattr(entry, name)) for name in field_names}
    fields["kind"] = kind
    fields["v"] = FORMAT_VERSION
    return json.dumps(fields, sort_keys=True, separators=(",", ":"))


def _to_json_value(value: object) -> object:
    """Return ``value`` in its one fixed JSON spelling.

    Timestamps are converted to UTC because the database hands them back in
    UTC; without this, hashing before saving and after reading would differ.
    """
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("Cannot stringify a timestamp without a time zone")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, StrEnum):
        return value.value
    return value
