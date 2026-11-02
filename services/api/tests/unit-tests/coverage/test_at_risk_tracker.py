from datetime import timedelta

from src.services.station_coverage.at_risk_tracker import AtRiskTracker

THRESHOLD = timedelta(minutes=15)


def test_area_counts_once_when_it_crosses_the_threshold(station_report, now):
    tracker = AtRiskTracker()
    report = station_report(
        "marmorkirken", covered_now=False, as_of=now, last_covered_at=now
    )

    assert tracker.observe([report], now + timedelta(minutes=44), THRESHOLD) == 0
    assert tracker.observe([report], now + timedelta(minutes=45), THRESHOLD) == 1
    assert tracker.observe([report], now + timedelta(minutes=50), THRESHOLD) == 0
    assert tracker.total == 1


def test_covered_area_is_never_counted(station_report, now):
    tracker = AtRiskTracker()
    report = station_report(
        "kongens-nytorv", covered_now=True, as_of=now, last_covered_at=None
    )

    assert tracker.observe([report], now + timedelta(hours=3), THRESHOLD) == 0
    assert tracker.total == 0


def test_rescued_area_counts_again_in_a_new_episode(station_report, now):
    tracker = AtRiskTracker()

    first = station_report(
        "marmorkirken", covered_now=False, as_of=now, last_covered_at=now
    )
    assert tracker.observe([first], now + timedelta(minutes=45), THRESHOLD) == 1

    rescued_at = now + timedelta(minutes=50)
    second = station_report(
        "marmorkirken", covered_now=False, as_of=rescued_at, last_covered_at=rescued_at
    )
    assert tracker.observe([second], rescued_at + timedelta(minutes=44), THRESHOLD) == 0
    assert tracker.observe([second], rescued_at + timedelta(minutes=45), THRESHOLD) == 1
    assert tracker.total == 2


def test_reset_for_new_shift_starts_from_zero(station_report, now):
    tracker = AtRiskTracker()
    report = station_report(
        "marmorkirken", covered_now=False, as_of=now, last_covered_at=now
    )
    tracker.observe([report], now + timedelta(minutes=45), THRESHOLD)

    tracker.reset_for_new_shift(now + timedelta(hours=8))

    assert tracker.total == 0
    assert tracker.shift_start == now + timedelta(hours=8)
    assert tracker.observe([report], now + timedelta(minutes=45), THRESHOLD) == 1


def test_two_stations_count_independently(station_report, now):
    tracker = AtRiskTracker()
    reports = [
        station_report(
            "marmorkirken", covered_now=False, as_of=now, last_covered_at=now
        ),
        station_report(
            "kongens-nytorv", covered_now=False, as_of=now, last_covered_at=now
        ),
    ]

    assert tracker.observe(reports, now + timedelta(minutes=45), THRESHOLD) == 2
    assert tracker.observe(reports, now + timedelta(minutes=46), THRESHOLD) == 0
    assert tracker.total == 2
