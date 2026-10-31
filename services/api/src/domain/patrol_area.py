"""Kinds of patrol area."""

from enum import StrEnum


class AreaKind(StrEnum):
    """The kinds of area at a station that must be patrolled."""

    CONCOURSE = "concourse"
    PLATFORM = "platform"
