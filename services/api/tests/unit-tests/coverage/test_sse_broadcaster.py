from src.services.station_coverage.sse_broadcaster import SseCoverageBroadcaster


def test_subscriber_starts_with_empty_queue():
    broadcaster = SseCoverageBroadcaster()

    queue = broadcaster.subscribe()

    assert queue.qsize() == 0


def test_publish_reaches_every_subscriber(station_report, now):
    broadcaster = SseCoverageBroadcaster()
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

    assert first.qsize() == 1
    assert second.qsize() == 1
    assert [r.station_id for r in first.get_nowait()] == [
        "marmorkirken",
        "kongens-nytorv",
    ]
    assert [r.station_id for r in second.get_nowait()] == [
        "marmorkirken",
        "kongens-nytorv",
    ]


def test_unsubscribed_dashboard_stops_receiving(station_report, now):
    broadcaster = SseCoverageBroadcaster()
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
