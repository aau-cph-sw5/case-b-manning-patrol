import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest


@pytest.fixture
def valid_connected_event():
    return {
        "android_id": str(uuid.uuid4()),
        "beacon_id": "550e8400-e29b-41d4-a716-000000000002",
        "event": "CONNECTED",
        "timestamp": "2026-05-30T03:08:13.000Z",
    }


@pytest.fixture
def valid_disconnected_event():
    return {
        "android_id": str(uuid.uuid4()),
        "beacon_id": "550e8400-e29b-41d4-a716-000000000002",
        "event": "DISCONNECTED",
        "timestamp": "2026-05-30T03:09:20.000Z",
    }


@pytest.fixture
def valid_event_with_debugging_number():
    return {
        "debugging_number": 1,
        "android_id": str(uuid.uuid4()),
        "beacon_id": "550e8400-e29b-41d4-a716-000000000002",
        "event": "CONNECTED",
        "timestamp": "2026-05-30T03:08:13.000Z",
    }


class TestEventFormat:
    def test_valid_connected_event_has_all_required_fields(self, valid_connected_event):
        assert "android_id" in valid_connected_event
        assert "beacon_id" in valid_connected_event
        assert "event" in valid_connected_event
        assert "timestamp" in valid_connected_event

    def test_valid_disconnected_event_has_all_required_fields(
        self, valid_disconnected_event
    ):
        assert "android_id" in valid_disconnected_event
        assert "beacon_id" in valid_disconnected_event
        assert "event" in valid_disconnected_event
        assert "timestamp" in valid_disconnected_event

    def test_event_is_json_serializable(self, valid_connected_event):
        json_str = json.dumps(valid_connected_event)
        assert isinstance(json_str, str)
        assert json.loads(json_str) == valid_connected_event

    def test_android_id_is_string(self, valid_connected_event):
        assert isinstance(valid_connected_event["android_id"], str)
        assert len(valid_connected_event["android_id"]) > 0

    def test_beacon_id_is_string(self, valid_connected_event):
        assert isinstance(valid_connected_event["beacon_id"], str)
        assert len(valid_connected_event["beacon_id"]) > 0

    def test_timestamp_is_iso_8601_format(self, valid_connected_event):
        timestamp = valid_connected_event["timestamp"]
        assert isinstance(timestamp, str)
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert parsed.tzinfo == UTC

    def test_optional_debugging_number_is_allowed(
        self, valid_event_with_debugging_number
    ):
        assert "debugging_number" in valid_event_with_debugging_number
        assert isinstance(valid_event_with_debugging_number["debugging_number"], int)


class TestEventType:
    def test_connected_event_type_is_valid(self, valid_connected_event):
        assert valid_connected_event["event"] == "CONNECTED"

    def test_disconnected_event_type_is_valid(self, valid_disconnected_event):
        assert valid_disconnected_event["event"] == "DISCONNECTED"

    def test_event_type_is_case_sensitive(self):
        event = {
            "android_id": "test",
            "beacon_id": "test",
            "event": "connected",
            "timestamp": "2026-05-30T03:08:13.000Z",
        }
        assert event["event"] not in ["CONNECTED", "DISCONNECTED"]


class TestTimestamp:
    def test_timestamp_format_with_z_suffix(self):
        event = {
            "android_id": "test",
            "beacon_id": "test",
            "event": "CONNECTED",
            "timestamp": "2026-05-30T03:08:13.000Z",
        }
        assert event["timestamp"].endswith("Z")

    def test_timestamp_can_be_parsed(self):
        timestamp_str = "2026-05-30T03:08:13.000Z"
        parsed = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        assert parsed.year == 2026
        assert parsed.month == 5
        assert parsed.day == 30

    def test_timestamp_includes_milliseconds(self):
        event = {
            "android_id": "test",
            "beacon_id": "test",
            "event": "CONNECTED",
            "timestamp": "2026-05-30T03:08:13.000Z",
        }
        assert "." in event["timestamp"]
        parts = event["timestamp"].split(".")
        milliseconds_part = parts[1].split("Z")[0]
        assert len(milliseconds_part) == 3

    def test_multiple_timestamps_are_chronological(self):
        events = [
            {
                "android_id": "test",
                "beacon_id": "b1",
                "event": "CONNECTED",
                "timestamp": "2026-05-30T03:08:13.000Z",
            },
            {
                "android_id": "test",
                "beacon_id": "b1",
                "event": "DISCONNECTED",
                "timestamp": "2026-05-30T03:08:50.000Z",
            },
            {
                "android_id": "test",
                "beacon_id": "b2",
                "event": "CONNECTED",
                "timestamp": "2026-05-30T03:09:00.000Z",
            },
        ]
        timestamps = [
            datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
            for e in events
        ]
        for earlier, later in zip(timestamps, timestamps[1:], strict=False):
            assert earlier < later


class TestBeaconID:
    def test_beacon_id_is_not_empty(self):
        event = {
            "android_id": "test",
            "beacon_id": "550e8400-e29b-41d4-a716-000000000002",
            "event": "CONNECTED",
            "timestamp": "2026-05-30T03:08:13.000Z",
        }
        assert len(event["beacon_id"]) > 0

    def test_beacon_id_can_be_uuid_format(self):
        beacon_uuid = str(uuid.uuid4())
        assert len(beacon_uuid) == 36

    def test_beacon_id_can_be_custom_format(self):
        event = {
            "android_id": "test",
            "beacon_id": "station_1_platform_A",
            "event": "CONNECTED",
            "timestamp": "2026-05-30T03:08:13.000Z",
        }
        assert event["beacon_id"] == "station_1_platform_A"


class TestAndroidID:
    def test_android_id_is_not_empty(self):
        event = {
            "android_id": "660e8400-e29b-41d4-a716-446655440001",
            "beacon_id": "test",
            "event": "CONNECTED",
            "timestamp": "2026-05-30T03:08:13.000Z",
        }
        assert len(event["android_id"]) > 0

    def test_android_id_is_uuid_format(self):
        android_uuid = str(uuid.uuid4())
        uuid.UUID(android_uuid)


class TestFixtureFile:
    def test_fixture_events_file_exists(self):
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        fixture_path = fixtures_dir / "fixture-events-v1.json"
        assert fixture_path.exists()

    def test_fixture_events_are_valid(self):
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        fixture_path = fixtures_dir / "fixture-events-v1.json"
        with open(fixture_path) as f:
            events = json.load(f)
        assert isinstance(events, list)
        assert len(events) > 0
        for event in events:
            assert "android_id" in event
            assert "beacon_id" in event
            assert "event" in event
            assert "timestamp" in event
            assert event["event"] in ["CONNECTED", "DISCONNECTED"]
            assert event["timestamp"].endswith("Z")
            datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))

    def test_fixture_has_both_event_types(self):
        fixtures_dir = Path(__file__).parent.parent / "fixtures"
        fixture_path = fixtures_dir / "fixture-events-v1.json"
        with open(fixture_path) as f:
            events = json.load(f)
        event_types = {e["event"] for e in events}
        assert "CONNECTED" in event_types
        assert "DISCONNECTED" in event_types


class TestEventSequence:
    def test_connected_before_disconnected_for_same_beacon(self):
        events = [
            {
                "android_id": "test",
                "beacon_id": "b1",
                "event": "CONNECTED",
                "timestamp": "2026-05-30T03:08:13.000Z",
            },
            {
                "android_id": "test",
                "beacon_id": "b1",
                "event": "DISCONNECTED",
                "timestamp": "2026-05-30T03:08:50.000Z",
            },
        ]
        connected_idx = None
        disconnected_idx = None
        for i, e in enumerate(events):
            if e["beacon_id"] == "b1" and e["event"] == "CONNECTED":
                connected_idx = i
            if e["beacon_id"] == "b1" and e["event"] == "DISCONNECTED":
                disconnected_idx = i
        assert connected_idx is not None
        assert disconnected_idx is not None
        assert connected_idx < disconnected_idx

    def test_multiple_beacons_can_be_connected_simultaneously(self):
        now = "2026-05-30T03:08:13.000Z"
        events = [
            {
                "android_id": "test",
                "beacon_id": "b1",
                "event": "CONNECTED",
                "timestamp": now,
            },
            {
                "android_id": "test",
                "beacon_id": "b2",
                "event": "CONNECTED",
                "timestamp": now,
            },
            {
                "android_id": "test",
                "beacon_id": "b3",
                "event": "CONNECTED",
                "timestamp": now,
            },
        ]
        connected_beacons = {
            e["beacon_id"] for e in events if e["event"] == "CONNECTED"
        }
        assert len(connected_beacons) == 3
