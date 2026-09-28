from manning_patrol_backend.services.positioning_service import (
    get_event_delay,
    load_fixture,
)


def test_get_event_delay_scales_by_speed():
    previous = {"timestamp": "2026-05-30T03:08:13.000Z"}
    current = {"timestamp": "2026-05-30T03:08:23.000Z"}

    delay = get_event_delay(previous, current)

    assert delay == 0.1  # 10 seconds divided by SPEED (100)


def test_get_event_delay_zero_for_same_timestamp():
    event = {"timestamp": "2026-05-30T03:08:13.000Z"}

    assert get_event_delay(event, event) == 0.0


def test_load_fixture_returns_empty_list_for_missing_file():
    assert load_fixture("does-not-exist.json") == []


def test_load_fixture_reads_fixture_events():
    events = load_fixture("fixture-events-v1.json")

    assert isinstance(events, list)
    assert len(events) > 0
    assert "timestamp" in events[0]
