import datetime

import pytest

from src.domain.coverage import OverdueEpisode


@pytest.fixture
def open_episode():
    now = datetime.datetime.now()
    overdue_at = now - datetime.timedelta(minutes=5)
    return OverdueEpisode(overdue_at=overdue_at, cleared_at=None)


@pytest.fixture
def closed_episode():
    now = datetime.datetime.now()
    overdue_at = now - datetime.timedelta(minutes=5)
    cleared_at = now - datetime.timedelta(minutes=1)
    return OverdueEpisode(overdue_at=overdue_at, cleared_at=cleared_at)


def test_is_open(open_episode, closed_episode):
    assert open_episode.is_open() is True
    assert closed_episode.is_open() is False


def test_duration_open(open_episode, closed_episode, now):
    assert open_episode.duration(now) == now - open_episode.overdue_at


def test_duration_closed(open_episode, closed_episode, now):
    assert closed_episode.duration(now) == datetime.timedelta(minutes=4)
