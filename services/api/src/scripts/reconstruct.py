"""Print the compliance picture of a past shift, rebuilt from the stored record.

Run with ``uv run reconstruct --date YYYY-MM-DD``. ``--known-at`` limits the
picture to events the backend had received by that time, and ``--json``
prints machine-readable output instead of a table. The database is only read,
never written.
"""

import argparse
import asyncio
import json
import sys
from datetime import UTC, date, datetime, timedelta, tzinfo
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import engine
from src.domain.compliance import CompliancePicture
from src.domain.coverage import AreaCoverageReport, OverdueEpisode
from src.domain.train_manning import TrainManningReport
from src.services.compliance.reconstruction import ComplianceReconstructor
from src.services.shared.interval_builder import IntervalBuilder
from src.services.shared.shift_schedule import ShiftSchedule
from src.services.station_coverage.coverage_service import CoverageService
from src.services.station_coverage.coverage_window import (
    MIN_QUALIFYING_DURATIONS,
    TIME_UNTIL_NEXT_NEEDED_PATROL,
    CoverageWindow,
)
from src.services.train_manning.train_manning_evaluator import TrainManningEvaluator
from src.services.train_manning.train_manning_service import TrainManningService


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line; exit with a usage error on invalid input."""
    parser = argparse.ArgumentParser(
        prog="reconstruct",
        description="Rebuild station coverage and train manning for a past shift.",
    )
    parser.add_argument(
        "--date",
        required=True,
        type=date.fromisoformat,
        help="local date the shift starts on, e.g. 2026-11-03",
    )
    parser.add_argument(
        "--known-at",
        type=_aware_datetime,
        help=(
            "only use events received by this time, as an ISO datetime with "
            "timezone, e.g. 2026-11-03T05:30+01:00"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print JSON instead of a table",
    )
    return parser.parse_args(argv)


def _aware_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError(
            f"{value!r} has no timezone; add one, e.g. +01:00 or Z",
        )
    return parsed


def build_reconstructor(shift_schedule: ShiftSchedule) -> ComplianceReconstructor:
    """Build the reconstructor with the same rules the live dashboard uses."""
    builder = IntervalBuilder()
    rule = CoverageWindow(
        time_until_next_needed_patrol=TIME_UNTIL_NEXT_NEEDED_PATROL,
        min_qualifying_durations=MIN_QUALIFYING_DURATIONS,
    )
    return ComplianceReconstructor(
        coverage_service=CoverageService(builder, rule),
        manning_service=TrainManningService(builder, TrainManningEvaluator()),
        shift_schedule=shift_schedule,
    )


async def _reconstruct(
    reconstructor: ComplianceReconstructor,
    day: date,
    known_at: datetime | None,
) -> CompliancePicture:
    try:
        async with AsyncSession(engine) as session:
            return await reconstructor.reconstruct(
                session,
                day,
                current_time=datetime.now(UTC),
                known_at=known_at,
            )
    finally:
        await engine.dispose()


def picture_to_dict(picture: CompliancePicture) -> dict[str, Any]:
    """Return the picture as JSON-ready data, with times in UTC ISO format."""
    return {
        "shift": {
            "start": _iso(picture.shift.start),
            "end": _iso(picture.shift.end),
        },
        "as_of": _iso(picture.as_of),
        "known_at": _iso(picture.known_at) if picture.known_at else None,
        "stations": [
            {
                "station_id": station.station_id,
                "status": station.coverage_status.value,
                "areas": [_area_to_dict(area) for area in station.areas],
            }
            for station in picture.stations
        ],
        "trains": [_train_to_dict(train) for train in picture.trains],
    }


def _area_to_dict(area: AreaCoverageReport) -> dict[str, Any]:
    return {
        "area_id": area.area.area_id,
        "kind": area.area.kind.value,
        "status": area.coverage_status.value,
        "overdue_episodes": [
            {
                "overdue_at": _iso(episode.overdue_at),
                "cleared_at": _iso(episode.cleared_at) if episode.cleared_at else None,
            }
            for episode in area.episodes
        ],
    }


def _train_to_dict(train: TrainManningReport) -> dict[str, Any]:
    return {
        "slug": train.train.slug,
        "manned_seconds": int(train.manned_time.total_seconds()),
        "running_seconds": int(train.running_time.total_seconds()),
        "manned_ratio": train.manned_ratio,
    }


def format_picture(picture: CompliancePicture, timezone: tzinfo) -> str:
    """Return the picture as a readable report, with times in ``timezone``."""
    lines = [
        f"Shift   {_local(picture.shift.start, timezone)}"
        f" - {_local(picture.shift.end, timezone)}",
        f"As of   {_local(picture.as_of, timezone)}",
        "Events  "
        + (
            f"received by {_local(picture.known_at, timezone)}"
            if picture.known_at
            else "all stored events"
        ),
        "",
        "Stations",
    ]
    if not picture.stations:
        lines.append("  (none)")
    for station in picture.stations:
        lines.append(f"  {station.station_id}  {station.coverage_status.value}")
        for area in station.areas:
            lines.append(
                f"    {area.area.area_id} ({area.area.kind.value})"
                f"  {len(area.episodes)} overdue episode(s)",
            )
            lines.extend(
                f"      {_episode(episode, picture.as_of, timezone)}"
                for episode in area.episodes
            )

    lines += ["", "Trains"]
    if not picture.trains:
        lines.append("  (none)")
    for train in picture.trains:
        ratio = train.manned_ratio
        lines.append(
            f"  {train.train.slug}  {_duration(train.manned_time)}"
            f" / {_duration(train.running_time)}"
            f"  {'n/a' if ratio is None else f'{ratio:.0%}'}",
        )
    return "\n".join(lines)


def _episode(episode: OverdueEpisode, as_of: datetime, timezone: tzinfo) -> str:
    end = (
        _local(episode.cleared_at, timezone) if episode.cleared_at else "still overdue"
    )
    return (
        f"{_local(episode.overdue_at, timezone)} - {end}"
        f"  ({_duration(episode.duration(as_of))})"
    )


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat()


def _local(moment: datetime, timezone: tzinfo) -> str:
    return moment.astimezone(timezone).strftime("%Y-%m-%d %H:%M:%S %Z")


def _duration(span: timedelta) -> str:
    minutes, seconds = divmod(int(span.total_seconds()), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h{minutes:02d}m{seconds:02d}s"


def main(argv: list[str] | None = None) -> None:
    """Reconstruct the shift from the command line and print it.

    Reads the database from DATABASE_URL. Exits with status 1 if the shift
    had not started yet.
    """
    args = parse_args(argv)
    shift_schedule = ShiftSchedule.from_file()
    reconstructor = build_reconstructor(shift_schedule)
    try:
        picture = asyncio.run(_reconstruct(reconstructor, args.date, args.known_at))
    except ValueError as error:
        print(f"reconstruct: {error}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(picture_to_dict(picture), indent=2))
    else:
        print(format_picture(picture, shift_schedule.timezone))


if __name__ == "__main__":
    main()
