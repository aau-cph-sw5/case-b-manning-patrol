from datetime import datetime

import pytest

from src.models.coverage import TimeSpan


def test_touches_returns_true_when_overlap():

    span1 = TimeSpan(datetime(2026, 1, 1, 12, 0, 0), datetime(2026, 1, 1, 12, 0, 5))

    span2 = TimeSpan(datetime(2026, 1, 1, 12, 0, 4), datetime(2026, 1, 1, 13, 0, 6))

    assert span1.touches(span2)
    assert span2.touches(span1)


def test_touches_returns_true_when_touches():

    span1 = TimeSpan(datetime(2026, 1, 1, 12, 0, 0), datetime(2026, 1, 1, 12, 0, 5))

    span2 = TimeSpan(datetime(2026, 1, 1, 12, 0, 5), datetime(2026, 1, 1, 13, 0, 6))

    assert span1.touches(span2)
    assert span2.touches(span1)


def test_touches_returns_false_when_no_overlap():

    span1 = TimeSpan(datetime(2026, 1, 1, 12, 0, 0), datetime(2026, 1, 1, 12, 0, 5))

    span2 = TimeSpan(datetime(2026, 1, 1, 12, 0, 6), datetime(2026, 1, 1, 13, 0, 10))

    assert not span1.touches(span2)
    assert not span2.touches(span1)


def test_merge_raises_value_error_when_no_overlap():

    span1 = TimeSpan(datetime(2026, 1, 1, 12, 0, 0), datetime(2026, 1, 1, 12, 0, 5))

    span2 = TimeSpan(datetime(2026, 1, 1, 12, 0, 6), datetime(2026, 1, 1, 13, 0, 10))

    with pytest.raises(ValueError):
        span1.merge(span2)

    with pytest.raises(ValueError):
        span2.merge(span1)


def test_merge_returns_timespan_when_overlap():

    span1 = TimeSpan(datetime(2026, 1, 1, 12, 0, 0), datetime(2026, 1, 1, 12, 0, 5))

    span2 = TimeSpan(datetime(2026, 1, 1, 12, 0, 4), datetime(2026, 1, 1, 13, 0, 6))

    assert span1.merge(span2) == TimeSpan(
        datetime(2026, 1, 1, 12, 0, 0), datetime(2026, 1, 1, 13, 0, 6)
    )

    assert span2.merge(span1) == TimeSpan(
        datetime(2026, 1, 1, 12, 0, 0), datetime(2026, 1, 1, 13, 0, 6)
    )
