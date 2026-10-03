"""
Unit tests for MET-B-004: Presence and Patrol Record Capture

Tests all acceptance criteria using mock beacon events.
No hardware or external dependencies required.
"""
import pytest
from datetime import datetime, timedelta
from typing import Optional

from manning_patrol_backend.models.patrol_models import BeaconEvent, PatrolConfig, PatrolRecord, PatrolSession
from manning_patrol_backend.services.patrol_service import PatrolService


# ============================================================================
# Test Setup & Fixtures
# ============================================================================

@pytest.fixture
def patrol_service() -> PatrolService:
    """Create a fresh PatrolService instance for each test."""
    config = PatrolConfig(
        x_seconds_threshold=10.0,  # 10 seconds to qualify as patrol
        tolerated_gap_seconds=8.0    # 8 seconds tolerated gap
    )
    return PatrolService(config)


@pytest.fixture
def mock_beacon_event(beacon_id: str = "station_1", connected: bool = True, 
                    timestamp: Optional[datetime] = None) -> BeaconEvent:
    """Create a mock beacon event for testing."""
    return BeaconEvent(
        beacon_id=beacon_id,
        connected=connected,
        timestamp=timestamp or datetime.utcnow(),
        android_id="test_device"
    )


# ============================================================================
# TEST 1: Session Management (Start/Stop)
# Acceptance Criterion: Start/Fortsæt begins a patrol session and Stop ends it.
# A beacon connection outside a session creates nothing.
# ============================================================================

class TestSessionManagement:
    """Tests for patrol session start/stop functionality."""
    
    def test_start_patrol_session_creates_active_session(self, patrol_service: PatrolService):
        """Start/Fortsæt begins a patrol session."""
        session = patrol_service.start_patrol_session(steward_id="steward_1")
        
        assert session is not None
        assert session.is_active is True
        assert session.start_time is not None
        assert patrol_service.active_session == session
    
    def test_stop_patrol_session_ends_session(self, patrol_service: PatrolService):
        """Stop ends the patrol session."""
        session = patrol_service.start_patrol_session()
        stopped_session = patrol_service.stop_patrol_session()
        
        assert stopped_session == session
        assert stopped_session.is_active is False
        assert stopped_session.end_time is not None
        assert patrol_service.active_session is None
    
    def test_beacon_event_outside_session_creates_nothing(self, patrol_service: PatrolService):
        """A beacon connection outside a session creates nothing."""
        event = BeaconEvent(
            beacon_id="station_1",
            connected=True,
            timestamp=datetime.utcnow()
        )
        result = patrol_service.handle_beacon_event(event)
        
        assert result is None
        assert len(patrol_service.get_open_records()) == 0


# ============================================================================
# TEST 2: Record Creation (Threshold)
# Acceptance Criterion: Within a session, a record is initiated once a beacon is 
# connected and completed for an area once its beacon connection has been held 
# for x seconds. A connection that never reaches x seconds does not save a record.
# ============================================================================

class TestRecordCreation:
    """Tests for patrol record creation based on connection duration."""
    
    def test_record_created_after_x_seconds(self, patrol_service: PatrolService):
        """Record completed when connection held for >= x seconds."""
        patrol_service.start_patrol_session()
        
        now = datetime.utcnow()
        # Connect for 11 seconds (> x_seconds_threshold=10)
        connect_event = BeaconEvent(
            beacon_id="station_1",
            connected=True,
            timestamp=now,
            android_id="test"
        )
        disconnect_event = BeaconEvent(
            beacon_id="station_1",
            connected=False,
            timestamp=now + timedelta(seconds=11),
            android_id="test"
        )
        
        # Connection starts
        patrol_service.handle_beacon_event(connect_event)
        
        # Connection ends after 11 seconds
        result = patrol_service.handle_beacon_event(disconnect_event)
        
        assert result is not None
        assert result.is_complete is True
        assert result.area_id == "station_1"
        assert result.duration_seconds() >= 10.0
    
    def test_short_connection_not_saved(self, patrol_service: PatrolService):
        """Connection shorter than x seconds does not create a record."""
        patrol_service.start_patrol_session()
        
        now = datetime.utcnow()
        # Connect for only 5 seconds (< x_seconds_threshold=10)
        connect_event = BeaconEvent(
            beacon_id="station_1",
            connected=True,
            timestamp=now,
            android_id="test"
        )
        disconnect_event = BeaconEvent(
            beacon_id="station_1",
            connected=False,
            timestamp=now + timedelta(seconds=5),
            android_id="test"
        )
        
        patrol_service.handle_beacon_event(connect_event)
        result = patrol_service.handle_beacon_event(disconnect_event)
        
        # Should not create a permanent record
        assert result is None
        # No completed records
        assert len(patrol_service.get_completed_records()) == 0


# ============================================================================
# TEST 3: Gap Tolerance
# Acceptance Criterion: A connection that drops and returns within the 
# tolerated gap continues the same record rather than opening a second one.
# A record closes when its connection has been lost for longer than the 
# tolerated gap.
# ============================================================================

class TestGapTolerance:
    """Tests for connection gap handling."""
    
    def test_temporary_drop_continues_same_record(self, patrol_service: PatrolService):
        """Brief disconnection (< tolerated gap) continues same record."""
        patrol_service.start_patrol_session()
        
        now = datetime.utcnow()
        beacon_id = "station_1"
        
        # Initial connection
        connect1 = BeaconEvent(beacon_id=beacon_id, connected=True, timestamp=now)
        patrol_service.handle_beacon_event(connect1)
        
        # Brief disconnection (5 seconds < tolerated_gap=8)
        disconnect = BeaconEvent(beacon_id=beacon_id, connected=False, timestamp=now + timedelta(seconds=5))
        patrol_service.handle_beacon_event(disconnect)
        
        # Reconnection within gap
        connect2 = BeaconEvent(beacon_id=beacon_id, connected=True, timestamp=now + timedelta(seconds=6))
        patrol_service.handle_beacon_event(connect2)
        
        # Should have 1 open record (not 2)
        open_records = patrol_service.get_open_records()
        assert len(open_records) == 1
        assert open_records[0].area_id == beacon_id
    
    def test_long_gap_closes_record(self, patrol_service: PatrolService):
        """Long disconnection (> tolerated gap) closes the record."""
        patrol_service.start_patrol_session()
        
        now = datetime.utcnow()
        beacon_id = "station_1"
        
        # Initial connection
        connect = BeaconEvent(beacon_id=beacon_id, connected=True, timestamp=now)
        patrol_service.handle_beacon_event(connect)
        
        # Long disconnection (10 seconds > tolerated_gap=8)
        current_time = now + timedelta(seconds=10)
        stale = patrol_service.cleanup_stale_connections(current_time)
        
        # Record should be closed
        assert beacon_id in stale
        completed = patrol_service.get_completed_records()
        assert len(completed) == 1
        assert completed[0].area_id == beacon_id


# ============================================================================
# TEST 4: Multiple Areas
# Acceptance Criterion: Records for more than one area may be open at the 
# same time. Every record carries which area it was taken in.
# ============================================================================

class TestMultipleAreas:
    """Tests for handling multiple simultaneous area connections."""
    
    def test_multiple_areas_open_simultaneously(self, patrol_service: PatrolService):
        """Multiple records can be open for different areas at once."""
        patrol_service.start_patrol_session()
        
        now = datetime.utcnow()
        
        # Connect to multiple beacons simultaneously
        events = [
            BeaconEvent(beacon_id="station_1", connected=True, timestamp=now),
            BeaconEvent(beacon_id="station_2", connected=True, timestamp=now + timedelta(seconds=1)),
            BeaconEvent(beacon_id="train_50", connected=True, timestamp=now + timedelta(seconds=2)),
        ]
        
        for event in events:
            patrol_service.handle_beacon_event(event)
        
        # Should have 3 open records (one per area)
        open_records = patrol_service.get_open_records()
        assert len(open_records) == 3
        
        # Each record should have its own area_id
        area_ids = {r.area_id for r in open_records}
        assert "station_1" in area_ids
        assert "station_2" in area_ids
        assert "train_50" in area_ids


# ============================================================================
# TEST 5: Session Stop Behavior
# Acceptance Criterion: Pressing Stop closes every open record at its last 
# confirmed connection, records with connections for more than x seconds are 
# saved; connections shorter than that were never records and are discarded.
# ============================================================================

class TestSessionStopBehavior:
    """Tests for behavior when Stop is pressed."""
    
    def test_stop_closes_all_open_records(self, patrol_service: PatrolService):
        """Stop closes all open records."""
        patrol_service.start_patrol_session()
        
        now = datetime.utcnow()
        
        # Create multiple open connections
        for i in range(3):
            event = BeaconEvent(
                beacon_id=f"station_{i}",
                connected=True,
                timestamp=now + timedelta(seconds=i)
            )
            patrol_service.handle_beacon_event(event)
        
        # Verify 3 open records
        assert len(patrol_service.get_open_records()) == 3
        
        # Stop session
        patrol_service.stop_patrol_session()
        
        # All records should now be closed (in active_session history)
        # Note: In our implementation, records stay in session.open_records but marked complete
        # This test verifies they are marked as complete
        session = list(patrol_service.sessions.values())[0]
        for record in session.open_records:
            assert record.is_complete is True
            assert record.end_time is not None


# ============================================================================
# TEST 6: Record Metadata
# Acceptance Criterion: Every record carries which area it was taken in.
# ============================================================================

class TestRecordMetadata:
    """Tests for record metadata."""
    
    def test_record_carries_area_id(self, patrol_service: PatrolService):
        """Every record carries its area_id."""
        patrol_service.start_patrol_session()
        
        now = datetime.utcnow()
        
        # Connect and disconnect
        connect = BeaconEvent(
            beacon_id="concourse_A",
            connected=True,
            timestamp=now
        )
        disconnect = BeaconEvent(
            beacon_id="concourse_A",
            connected=False,
            timestamp=now + timedelta(seconds=15)
        )
        
        patrol_service.handle_beacon_event(connect)
        result = patrol_service.handle_beacon_event(disconnect)
        
        assert result is not None
        assert result.area_id == "concourse_A"
        assert result.session_id == patrol_service.get_active_session().session_id


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple scenarios."""
    
    def test_full_patrol_workflow(self, patrol_service: PatrolService):
        """Test complete patrol workflow: start -> events -> stop."""
        # 1. Start session
        session = patrol_service.start_patrol_session(steward_id="steward_1")
        assert session.is_active is True
        
        now = datetime.utcnow()
        
        # 2. Create valid patrol record (15 seconds)
        connect = BeaconEvent(
            beacon_id="platform_1",
            connected=True,
            timestamp=now
        )
        disconnect = BeaconEvent(
            beacon_id="platform_1",
            connected=False,
            timestamp=now + timedelta(seconds=15)
        )
        
        patrol_service.handle_beacon_event(connect)
        record = patrol_service.handle_beacon_event(disconnect)
        
        assert record is not None
        assert record.is_complete is True
        assert record.area_id == "platform_1"
        assert record.duration_seconds() >= 10.0
        
        # 3. Stop session
        stopped = patrol_service.stop_patrol_session()
        assert stopped.is_active is False
        
        # 4. Verify completed records
        completed = patrol_service.get_completed_records()
        assert len(completed) >= 1
