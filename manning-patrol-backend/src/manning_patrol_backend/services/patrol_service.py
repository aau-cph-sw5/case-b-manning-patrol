"""
MET-B-004: Presence and Patrol Record Capture Service

Handles patrol sessions and records based on beacon events.
Uses the positioning interface contract (MET-B-002) to receive events.
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..models.patrol_models import BeaconEvent, PatrolRecord, PatrolSession, PatrolConfig


class PatrolService:
    """
    Service for managing patrol sessions and records.
    Implements MET-B-004: Presence and patrol record capture.
    """
    
    def __init__(self, config: Optional[PatrolConfig] = None):
        self.config = config or PatrolConfig()
        self.active_session: Optional[PatrolSession] = None
        self.sessions: Dict[str, PatrolSession] = {}
        self.all_records: Dict[str, PatrolRecord] = {}
        # Track active connections per beacon for gap detection
        self.active_connections: Dict[str, datetime] = {}
    
    def start_patrol_session(self, steward_id: Optional[str] = None) -> PatrolSession:
        """
        Start a new patrol session.
        
        Acceptance Criterion: Start/Fortsæt begins a patrol session
        """
        session_id = str(uuid.uuid4())
        session = PatrolSession(
            session_id=session_id,
            start_time=datetime.utcnow(),
            steward_id=steward_id,
            is_active=True
        )
        self.active_session = session
        self.sessions[session_id] = session
        return session
    
    def stop_patrol_session(self) -> Optional[PatrolSession]:
        """
        Stop the current patrol session and close all open records.
        
        Acceptance Criterion: Stop ends the session. A beacon connection outside 
        a session creates nothing.
        """
        if self.active_session is None:
            return None
        
        session = self.active_session
        end_time = datetime.utcnow()
        session.close_all_records(end_time)
        self.active_session = None
        return session
    
    def handle_beacon_event(self, event: BeaconEvent) -> Optional[PatrolRecord]:
        """
        Handle a beacon connection/disconnection event.
        Creates records based on connection duration.
        
        Acceptance Criteria:
        - Within a session, a record is initiated once a beacon is connected
        - Completed for an area once beacon connection held for x seconds
        - Connection that never reaches x seconds does not save a record
        - Connection that drops and returns within tolerated gap continues same record
        - Connection lost for longer than tolerated gap closes the record
        - Records for more than one area may be open at the same time
        """
        if self.active_session is None:
            # Beacon connection outside a session creates nothing
            return None
        
        session = self.active_session
        beacon_id = event.beacon_id
        timestamp = event.timestamp
        
        if event.connected:
            # New connection - initiate record
            if beacon_id not in self.active_connections:
                record = PatrolRecord(
                    record_id=str(uuid.uuid4()),
                    area_id=beacon_id,
                    start_time=timestamp,
                    steward_id=session.steward_id,
                    session_id=session.session_id
                )
                session.add_record(record)
                self.all_records[record.record_id] = record
                self.active_connections[beacon_id] = timestamp
                return record
        else:
            # Connection lost - check duration
            if beacon_id in self.active_connections:
                start_time = self.active_connections[beacon_id]
                duration = (timestamp - start_time).total_seconds()
                
                if duration >= self.config.x_seconds_threshold:
                    # Record is complete - find and close it
                    for record in session.open_records:
                        if record.area_id == beacon_id and record.end_time is None:
                            record.end_time = timestamp
                            record.is_complete = True
                            del self.active_connections[beacon_id]
                            return record
                else:
                    # Connection was too short - discard
                    del self.active_connections[beacon_id]
        
        return None
    
    def check_gap_tolerance(self, beacon_id: str, current_time: datetime) -> bool:
        """
        Check if a connection drop is within the tolerated gap.
        
        Acceptance Criterion: A connection that drops and returns within the 
        tolerated gap continues the same record rather than opening a second one.
        """
        if beacon_id not in self.active_connections:
            return False
        
        last_connection = self.active_connections[beacon_id]
        gap_duration = (current_time - last_connection).total_seconds()
        return gap_duration <= self.config.tolerated_gap_seconds
    
    def get_open_records(self) -> List[PatrolRecord]:
        """Get all currently open (incomplete) records."""
        if self.active_session is None:
            return []
        return [r for r in self.active_session.open_records if not r.is_complete]
    
    def get_completed_records(self) -> List[PatrolRecord]:
        """Get all completed records from all sessions."""
        return [r for r in self.all_records.values() if r.is_complete]
    
    def get_active_session(self) -> Optional[PatrolSession]:
        """Get the current active patrol session, if any."""
        return self.active_session
    
    def get_session(self, session_id: str) -> Optional[PatrolSession]:
        """Get a specific session by ID."""
        return self.sessions.get(session_id)
    
    def cleanup_stale_connections(self, current_time: datetime) -> List[str]:
        """
        Close records where connection has been lost for longer than tolerated gap.
        
        Acceptance Criterion: A record closes when its connection has been lost 
        for longer than the tolerated gap, and its end time is the last confirmed connection.
        """
        stale_beacons = []
        for beacon_id, last_time in list(self.active_connections.items()):
            gap = (current_time - last_time).total_seconds()
            if gap > self.config.tolerated_gap_seconds:
                # Close the record for this beacon
                if self.active_session:
                    for record in self.active_session.open_records:
                        if record.area_id == beacon_id and record.end_time is None:
                            record.end_time = last_time  # Last confirmed connection
                            record.is_complete = True
                            stale_beacons.append(beacon_id)
                            break
        
        # Remove stale connections
        for beacon_id in stale_beacons:
            del self.active_connections[beacon_id]
        
        return stale_beacons
