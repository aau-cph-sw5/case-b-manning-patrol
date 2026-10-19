from src.services.coverage.sse_broadcaster import SseBroadcaster


def test_subscriber_starts_with_empty_queue():
    broadcaster = SseBroadcaster()

    queue = broadcaster.subscribe()

    assert queue.qsize() == 0


def test_publish_reaches_every_subscriber(station_report, now):
    broadcaster = SseBroadcaster()
    first = broadcaster.subscribe()
    second = broadcaster.subscribe()

    broadcaster.publish(
        [
            station_report(
                "marmorkirken", covered_now=True, as_of=now, last_covered_at=now
            ),
            station_report(
                "kongens-nytorv", covered_now=False, as_of=now, last_covered_at=None
            ),
        ]
    )

    assert first.qsize() == 2
    assert second.qsize() == 2
    assert first.get_nowait().station_id == "marmorkirken"
    assert second.get_nowait().station_id == "kongens-nytorv"


def test_unsubscribed_dashboard_stops_receiving(station_report, now):
    broadcaster = SseBroadcaster()
    gone = broadcaster.subscribe()
    staying = broadcaster.subscribe()
    broadcaster.unsubscribe(gone)

    broadcaster.publish(
        [
            station_report(
                "marmorkirken", covered_now=True, as_of=now, last_covered_at=now
            )
        ]
    )

    assert gone.qsize() == 0
    assert staying.qsize() == 1
