"""Unit tests for the argument parsing and output of the reconstruct command."""

import json
from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest

from src.domain.compliance import CompliancePicture
from src.domain.coverage import (
    AreaCoverageReport,
    AreaReference,
    OverdueEpisode,
    StationCoverageReport,
)
from src.domain.patrol_area import AreaKind
from src.domain.shift import Shift
from src.domain.train_manning import TrainManningReport, TrainReference
from src.scripts.reconstruct import format_picture, parse_args, picture_to_dict

COPENHAGEN = ZoneInfo("Europe/Copenhagen")
SHIFT = Shift(
    start=datetime(2026, 11, 2, 23, 0, tzinfo=UTC),
    end=datetime(2026, 11, 3, 5, 0, tzinfo=UTC),
)
OVERDUE_AT = datetime(2026, 11, 3, 0, 31, tzinfo=UTC)
CLEARED_AT = datetime(2026, 11, 3, 1, 0, 10, tzinfo=UTC)


def make_picture(known_at: datetime | None = None) -> CompliancePicture:
    area = AreaCoverageReport(
        area=AreaReference(station_id="STN-A", area_id="A-P", kind=AreaKind.PLATFORM),
        last_covered_at=None,
        covered_now=False,
        shift_start_time=SHIFT.start,
        current_steward_ids=frozenset(),
        episodes=(
            OverdueEpisode(overdue_at=OVERDUE_AT, cleared_at=CLEARED_AT),
            OverdueEpisode(overdue_at=CLEARED_AT + timedelta(hours=1), cleared_at=None),
        ),
        time_until_next_needed_patrol=timedelta(minutes=60),
        as_of=SHIFT.end,
    )
    train = TrainManningReport(
        train=TrainReference(
            train_id=UUID("770e8400-e29b-41d4-a716-446655440001"),
            slug="a29",
            beacon_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            line_ids=frozenset({"M1"}),
        ),
        running_time=timedelta(hours=6),
        manned_time=timedelta(hours=4, minutes=30),
        manned_now=False,
        current_steward_ids=frozenset(),
        as_of=SHIFT.end,
    )
    return CompliancePicture(
        shift=SHIFT,
        as_of=SHIFT.end,
        known_at=known_at,
        stations=(StationCoverageReport(station_id="STN-A", areas=(area,)),),
        trains=(train,),
    )


def test_parse_args_reads_date_and_known_at():
    args = parse_args(
        ["--date", "2026-11-03", "--known-at", "2026-11-03T05:30+01:00", "--json"]
    )

    assert args.date == date(2026, 11, 3)
    assert args.known_at == datetime(2026, 11, 3, 4, 30, tzinfo=UTC)
    assert args.json is True


def test_parse_args_known_at_is_optional():
    args = parse_args(["--date", "2026-11-03"])

    assert args.known_at is None
    assert args.json is False


def test_parse_args_rejects_known_at_without_timezone(capsys):
    with pytest.raises(SystemExit):
        parse_args(["--date", "2026-11-03", "--known-at", "2026-11-03T05:30"])

    assert "has no timezone" in capsys.readouterr().err


def test_parse_args_rejects_invalid_date():
    with pytest.raises(SystemExit):
        parse_args(["--date", "03-11-2026"])


def test_picture_to_dict_is_json_with_utc_times():
    data = json.loads(json.dumps(picture_to_dict(make_picture())))

    assert data["shift"] == {
        "start": "2026-11-02T23:00:00+00:00",
        "end": "2026-11-03T05:00:00+00:00",
    }
    assert data["known_at"] is None
    (station,) = data["stations"]
    assert station["status"] == "overdue"
    assert station["areas"][0]["overdue_episodes"] == [
        {
            "overdue_at": "2026-11-03T00:31:00+00:00",
            "cleared_at": "2026-11-03T01:00:10+00:00",
        },
        {"overdue_at": "2026-11-03T02:00:10+00:00", "cleared_at": None},
    ]
    assert data["trains"] == [
        {
            "slug": "a29",
            "manned_seconds": 16200,
            "running_seconds": 21600,
            "manned_ratio": 0.75,
        }
    ]


def test_picture_to_dict_includes_known_at():
    known_at = datetime(2026, 11, 3, 4, 0, tzinfo=UTC)

    data = picture_to_dict(make_picture(known_at=known_at))

    assert data["known_at"] == "2026-11-03T04:00:00+00:00"


def test_format_picture_shows_local_times_episodes_and_trains():
    text = format_picture(make_picture(), COPENHAGEN)

    assert "Shift   2026-11-03 00:00:00 CET - 2026-11-03 06:00:00 CET" in text
    assert "Events  all stored events" in text
    assert "A-P (platform)  2 overdue episode(s)" in text
    assert "2026-11-03 01:31:00 CET - 2026-11-03 02:00:10 CET  (0h29m10s)" in text
    assert "still overdue" in text
    assert "a29  4h30m00s / 6h00m00s  75%" in text


def test_format_picture_names_the_known_at_cutoff():
    known_at = datetime(2026, 11, 3, 4, 0, tzinfo=UTC)

    text = format_picture(make_picture(known_at=known_at), COPENHAGEN)

    assert "Events  received by 2026-11-03 05:00:00 CET" in text
