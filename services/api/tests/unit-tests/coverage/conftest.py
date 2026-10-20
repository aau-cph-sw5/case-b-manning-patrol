import datetime

import pytest


@pytest.fixture
def now():
    return datetime.datetime.now()
