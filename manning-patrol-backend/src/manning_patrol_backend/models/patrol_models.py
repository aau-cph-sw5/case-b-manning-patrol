"""
Data models for MET-B-004: Presence and Patrol Record Capture
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class BeaconEvent:
    """Represents a Bluetooth beacon connection/disconnection event."""
    beacon_id: str
    connected: bool
    timestamp: datetime
    android_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BeaconEvent':
        """Create BeaconEvent from dictionary (e.g., from WebSocket)."""
        return cls(
            beacon_id=data.get('beacon_id'),
            connected=data.get('connected'),
            timestamp=datetime.fromisoformat(data.get('timestamp').replace('Z', '+00:00')),
            android_id=data.get('android_id')
        )


@dataclass
class PatrolRecord:
    """Represents a completed or ongoing patrol record for a specific area."""
    record_id: str
    area_id: str  # Platform, concourse, or train identifier
    start_time: datetime
    end_time: Optional[datetime] = None
    steward_id: Optional[str] = None
    session_id: Optional[str] = None
    is_complete: bool = False
    
    def duration_seconds(self) -> float:
        """Calculate duration of record in seconds."""
        if self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()


@dataclass 
class PatrolSession:
    """Represents an active patrol session (Start -> Stop)."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    steward_id: Optional[str] = None
    is_active: bool = True
    open_records: List[PatrolRecord] = field(default_factory=list)
    
    def add_record(self, record: PatrolRecord) -> None:
        """Add a new record to the session."""
        self.open_records.append(record)
    
    def close_record(self, record_id: str, end_time: datetime) -> bool:
        """Close a specific record in the session."""
        for record in self.open_records:
            if record.record_id == record_id:
                record.end_time = end_time
                record.is_complete = True
                return True
        return False
    
    def close_all_records(self, end_time: datetime) -> None:
        """Close all open records when session ends."""
        for record in self.open_records:
            record.end_time = end_time
            record.is_complete = True
        self.is_active = False
        self.end_time = end_time


@dataclass
class PatrolConfig:
    """Configuration for patrol session settings."""
    x_seconds_threshold: float = 10.0  # Seconds to consider area as patrolled
    tolerated_gap_seconds: float = 8.0  # Max gap before record closes
