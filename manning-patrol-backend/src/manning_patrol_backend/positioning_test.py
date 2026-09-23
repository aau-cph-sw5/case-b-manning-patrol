import pytest
from pydantic import ValidationError

from manning_patrol_backend.services.positioning_service import observed_events, load_fixture

def test_observed_events():
    # Sample events for testing
    events = [
        {"beacon_id": "1", "event_type": "OBSERVED", "timestamp": "2024-01-01T10:00:00Z"},
        {"beacon_id": "2", "event_type": "OBSERVED", "timestamp": "2024-01-01T10:05:00Z"},
        {"beacon_id": "1", "event_type": "NOT_OBSERVED", "timestamp": "2024-01-01T10:10:00Z"},
        {"beacon_id": "3", "event_type": "OBSERVED", "timestamp": "2024-01-01T10:15:00Z"},
    ]

    # Test without as_of parameter
    result = observed_events(events)
    assert len(result) == 2  # Only beacon_id 2 and 3 should be observed

    # Test with as_of parameter
    result_as_of = observed_events(events, as_of="2024-01-01T10:07:00Z")
    assert len(result_as_of) == 2  # Only beacon_id 2 should be observed
    assert result_as_of[0]["beacon_id"] == "1"  # Beacon 1 was observed before the as_of time
    assert result_as_of[1]["beacon_id"] == "2"  # Beacon 2 was observed before the as_of time

        # Test with as_of parameter
    result_as_of = observed_events(events, as_of="2024-01-01T10:12:00Z")
    assert len(result_as_of) == 1  # Only beacon_id 2 should be observed
    assert result_as_of[0]["beacon_id"] == "2"  # Only Beacon 2 was observed before the as_of time
test_observed_events()