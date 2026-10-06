// mirrors ConnectionEvent in contracts/positioning-ingestion/v2: the exact payload the
// backend expects from POST /api/v2/connection/connect and /api/v2/connection/disconnect.
export type BeaconEventKind = "CONNECTED" | "DISCONNECTED";

export type BeaconEvent = {
  event: BeaconEventKind;
  beacon_id: string;
  android_id: string;
  // device time as ISO 8601 UTC with milliseconds, e.g. "2026-05-30T03:08:13.000Z".
  // the phone is the source of truth for event time (ADR-0004).
  timestamp: string;
};

// the app's view of the scan: what it currently knows about the beacons around it.
// named for the scan, not the beacons: the beacons' own state lives on them.
export type ScanState = {
  scanning: boolean;
  // beacon ids currently connected, in the order they connected.
  connectedBeaconIds: string[];
  // the most recent events, newest first.
  recentEvents: BeaconEvent[];
};

export const initialScanState: ScanState = {
  scanning: false,
  connectedBeaconIds: [],
  recentEvents: [],
};

// things that happened to the scan. events arrive from the scanner as it sees beacons.
export type ScanAction =
  | { type: "SCAN_STARTED" }
  | { type: "SCAN_STOPPED" }
  | { type: "EVENT_RECEIVED"; event: BeaconEvent };
