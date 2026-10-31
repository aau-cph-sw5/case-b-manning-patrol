from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.domain.train_manning import TrainManningReport, TrainReference
from src.services.train_manning.train_manning_publisher import (
    SseTrainManningBroadcaster,
)

NOW = datetime(2026, 10, 8, 12, 0, 0, tzinfo=UTC)
TRAIN_ID = UUID("10000000-0000-0000-0000-000000000001")
BEACON = UUID("00000000-0000-0000-0000-00000000a001")


def train_report(manned_now: bool = False) -> TrainManningReport:
    return TrainManningReport(
        train=TrainReference(
            id=TRAIN_ID, slug="a29", beacon_id=BEACON, line_ids=frozenset({"M1"})
        ),
        running_time=timedelta(hours=12),
        manned_time=timedelta(0),
        manned_now=manned_now,
        current_steward_ids=frozenset(),
        as_of=NOW,
    )


def test_subscriber_starts_with_empty_queue():
    broadcaster = SseTrainManningBroadcaster()

    queue = broadcaster.subscribe()

    assert queue.qsize() == 0


def test_publish_reaches_every_subscriber():
    broadcaster = SseTrainManningBroadcaster()
    first = broadcaster.subscribe()
    second = broadcaster.subscribe()

    broadcaster.publish([train_report(manned_now=True)])

    assert first.qsize() == 1
    assert second.qsize() == 1
    assert first.get_nowait()[0].manned_now is True
    assert second.get_nowait()[0].train.id == TRAIN_ID


def test_unsubscribed_dashboard_stops_receiving():
    broadcaster = SseTrainManningBroadcaster()
    gone = broadcaster.subscribe()
    staying = broadcaster.subscribe()
    broadcaster.unsubscribe(gone)

    broadcaster.publish([train_report()])

    assert gone.qsize() == 0
    assert staying.qsize() == 1
