import pytest

from src.scripts.seed import FIXTURE, build_adjustments, build_events, load_events
from src.services.positioning_service import load_fixture


def test_load_events_raises_for_missing_fixture():
    with pytest.raises(FileNotFoundError, match="does-not-exist.json"):
        load_events("does-not-exist.json")


def test_build_adjustments_raises_when_blip_event_missing():
    fixture = [
        entry for entry in load_fixture(FIXTURE) if entry["debugging_number"] != 10
    ]

    with pytest.raises(ValueError, match="event 10"):
        build_adjustments(build_events(fixture))


def test_build_adjustments_targets_blip_event():
    events = load_events(FIXTURE)

    adjustments = build_adjustments(events)

    assert len(adjustments) == 1
    assert adjustments[0].target_event_id in {e.event_id for e in events}
