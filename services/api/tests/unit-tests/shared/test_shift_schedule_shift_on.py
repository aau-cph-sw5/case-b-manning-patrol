"""Unit tests for ShiftSchedule.shift_on and ShiftSchedule.timezone."""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from src.domain.shift import Shift
from src.services.shared.shift_schedule import ShiftSchedule

COPENHAGEN = ZoneInfo("Europe/Copenhagen")


def night_schedule() -> ShiftSchedule:
    return ShiftSchedule(start=time(0, 0), end=time(6, 0), timezone=COPENHAGEN)


def test_shift_on_winter_date_is_one_hour_ahead_of_utc():
    shift = night_schedule().shift_on(date(2026, 11, 3))

    assert shift == Shift(
        start=datetime(2026, 11, 2, 23, 0, tzinfo=UTC),
        end=datetime(2026, 11, 3, 5, 0, tzinfo=UTC),
    )


def test_shift_on_summer_date_is_two_hours_ahead_of_utc():
    shift = night_schedule().shift_on(date(2026, 7, 3))

    assert shift == Shift(
        start=datetime(2026, 7, 2, 22, 0, tzinfo=UTC),
        end=datetime(2026, 7, 3, 4, 0, tzinfo=UTC),
    )


def test_shift_on_night_of_daylight_saving_change_is_one_hour_shorter():
    shift = night_schedule().shift_on(date(2026, 3, 29))

    assert shift.end - shift.start == timedelta(hours=5)


def test_shift_on_shift_past_midnight_ends_the_next_day():
    schedule = ShiftSchedule(start=time(22, 0), end=time(6, 0), timezone=COPENHAGEN)

    shift = schedule.shift_on(date(2026, 11, 3))

    assert shift == Shift(
        start=datetime(2026, 11, 3, 21, 0, tzinfo=UTC),
        end=datetime(2026, 11, 4, 5, 0, tzinfo=UTC),
    )


def test_shift_on_matches_latest_shift_during_that_shift():
    schedule = night_schedule()
    during = datetime(2026, 11, 3, 2, 0, tzinfo=UTC)

    assert schedule.shift_on(date(2026, 11, 3)) == schedule.latest_shift(during)


def test_timezone_is_the_schedule_timezone():
    assert night_schedule().timezone == COPENHAGEN
