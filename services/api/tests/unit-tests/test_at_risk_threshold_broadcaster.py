from src.services.config.at_risk_threshold_broadcaster import AtRiskThresholdBroadcaster


def test_current_is_the_initial_value():
    broadcaster = AtRiskThresholdBroadcaster(current_minutes=10)

    assert broadcaster.current() == 10


def test_subscriber_starts_with_empty_queue():
    broadcaster = AtRiskThresholdBroadcaster(current_minutes=10)

    queue = broadcaster.subscribe()

    assert queue.qsize() == 0


def test_publish_reaches_every_subscriber_and_updates_current():
    broadcaster = AtRiskThresholdBroadcaster(current_minutes=10)
    first = broadcaster.subscribe()
    second = broadcaster.subscribe()

    broadcaster.publish(25)

    assert broadcaster.current() == 25
    assert first.get_nowait() == 25
    assert second.get_nowait() == 25


def test_unsubscribed_stream_stops_receiving():
    broadcaster = AtRiskThresholdBroadcaster(current_minutes=10)
    gone = broadcaster.subscribe()
    staying = broadcaster.subscribe()
    broadcaster.unsubscribe(gone)

    broadcaster.publish(30)

    assert gone.qsize() == 0
    assert staying.get_nowait() == 30


def test_unsubscribe_ignores_unknown_queues():
    import asyncio

    broadcaster = AtRiskThresholdBroadcaster(current_minutes=10)

    broadcaster.unsubscribe(asyncio.Queue())

    assert broadcaster.current() == 10
