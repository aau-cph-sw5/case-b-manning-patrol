"""Unit tests for the manning percentages in TrainsUpdatePresenter."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.domain.train_manning import TrainManningReport, TrainReference
from src.services.train_manning.trains_update_presenter import TrainsUpdatePresenter

SENT_AT = datetime(2026, 9, 21, 10, 15, tzinfo=UTC)
TRAIN_ID = UUID("10000000-0000-0000-0000-000000000001")
BEACON = UUID("00000000-0000-0000-0000-00000000a001")


def hours(h: float) -> timedelta:
    return timedelta(hours=h)


def make_report(
    line_ids: frozenset[str],
    running: timedelta,
    manned: timedelta,
    train_id: UUID = TRAIN_ID,
) -> TrainManningReport:
    return TrainManningReport(
        train=TrainReference(
            train_id=train_id, slug="a29", beacon_id=BEACON, line_ids=line_ids
        ),
        running_time=running,
        manned_time=manned,
        manned_now=manned > timedelta(0),
        current_steward_ids=frozenset(),
        as_of=SENT_AT,
    )


def make_presenter() -> TrainsUpdatePresenter:
    return TrainsUpdatePresenter(trains=[], train_lines=[])


def test_overall_percent_is_manned_time_over_running_time():
    update = make_presenter().to_trains_update(
        [make_report(frozenset({"M1", "M2"}), running=hours(4), manned=hours(1))],
        sent_at=SENT_AT,
    )

    assert update.manning_percent == 25.0
    assert update.m1m2_manning_percent == 25.0
    assert update.m3m4_manning_percent == 0


def test_line_groups_are_computed_separately():
    update = make_presenter().to_trains_update(
        [
            make_report(
                frozenset({"M1"}), running=hours(2), manned=hours(2), train_id=TRAIN_ID
            ),
            make_report(
                frozenset({"M3"}),
                running=hours(2),
                manned=hours(0),
                train_id=UUID("10000000-0000-0000-0000-000000000002"),
            ),
        ],
        sent_at=SENT_AT,
    )

    assert update.manning_percent == 50.0
    assert update.m1m2_manning_percent == 100.0
    assert update.m3m4_manning_percent == 0


def test_train_counts_in_both_groups_when_its_lines_overlap():
    update = make_presenter().to_trains_update(
        [make_report(frozenset({"M1", "M3"}), running=hours(4), manned=hours(1))],
        sent_at=SENT_AT,
    )

    assert update.manning_percent == 25.0
    assert update.m1m2_manning_percent == 25.0
    assert update.m3m4_manning_percent == 25.0


def test_trains_in_the_same_group_are_aggregated():
    update = make_presenter().to_trains_update(
        [
            make_report(
                frozenset({"M2"}), running=hours(2), manned=hours(1), train_id=TRAIN_ID
            ),
            make_report(
                frozenset({"M2"}),
                running=hours(2),
                manned=hours(1),
                train_id=UUID("10000000-0000-0000-0000-000000000002"),
            ),
        ],
        sent_at=SENT_AT,
    )

    assert update.m1m2_manning_percent == 50.0
    assert update.manning_percent == 50.0


def test_percents_are_zero_when_there_is_no_running_time():
    update = make_presenter().to_trains_update([], sent_at=SENT_AT)

    assert update.manning_percent == 0
    assert update.m1m2_manning_percent == 0
    assert update.m3m4_manning_percent == 0
