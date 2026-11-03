/** Types for the beacon scan: the events a scanner reports and the state built from them. */

/** Whether a beacon came into or went out of range; picks the endpoint the event is posted to. */
export type BeaconEventKind = "CONNECTED" | "DISCONNECTED";

/**
 * One connect or disconnect as a scanner reports it.
 *
 * Not the wire format: `postConnectionEvent` sends it to
 * POST /api/v2/connection/connect or /api/v2/connection/disconnect as a
 * `ConnectionEvent` (contracts/api/v2/positioning-ingestion), choosing the
 * endpoint from `event`.
 */
export type BeaconConnectionEvent = {
  event: BeaconEventKind;
  beacon_id: string;
  /**
   * Device time as ISO 8601 UTC with milliseconds, e.g. "2026-05-30T03:08:13.000Z".
   * The phone is the source of truth for event time (ADR-0004).
   */
  timestamp: string;
};

/**
 * The app's view of the scan: what it currently knows about the beacons around
 * it. Named for the scan, not the beacons: the beacons' own state lives on them.
 */
export type ScanState = {
  scanning: boolean;
  /** Beacon ids currently connected, in the order they connected. */
  connectedBeaconIds: string[];
  /** The most recent events, newest first. */
  recentEvents: BeaconConnectionEvent[];
};

export const initialScanState: ScanState = {
  scanning: false,
  connectedBeaconIds: [],
  recentEvents: [],
};

/** Things that happened to the scan. Events arrive from the scanner as it sees beacons. */
export type ScanAction =
  | { type: "SCAN_STARTED" }
  | { type: "SCAN_STOPPED" }
  | { type: "EVENT_RECEIVED"; event: BeaconConnectionEvent };
