// mirrors ConnectionEvent in contracts/positioning-ingestion/v1: the exact payload the
// backend expects from POST /api/v1/connection/connect and /api/v1/connection/disconnect.
export type BeaconEventKind = "CONNECTED" | "DISCONNECTED";

export type BeaconEvent = {
  event: BeaconEventKind;
  beacon_id: string;
  android_id: string;
  // device time as ISO 8601 UTC with milliseconds, e.g. "2026-05-30T03:08:13.000Z".
  // the phone is the source of truth for event time (ADR-0004).
  timestamp: string;
};

export type BeaconState = {
  scanning: boolean;
  // beacon ids currently connected, in the order they connected.
  connectedBeaconIds: string[];
  // the most recent events, newest first.
  recentEvents: BeaconEvent[];
};

export const initialBeaconState: BeaconState = {
  scanning: false,
  connectedBeaconIds: [],
  recentEvents: [],
};

// things that happened to the scan. events arrive from the scanner as it sees beacons.
export type BeaconAction =
  | { type: "SCAN_STARTED" }
  | { type: "SCAN_STOPPED" }
  | { type: "EVENT_RECEIVED"; event: BeaconEvent };
