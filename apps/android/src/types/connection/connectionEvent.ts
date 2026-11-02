/** Wire type for beacon connection events. */

/**
 * Body of POST /api/v2/connection/connect and /api/v2/connection/disconnect,
 * the connection-event schema of contracts/api/v2/positioning-ingestion.
 */
export type ConnectionEvent = {
  beacon_id: string;
  /** UUID of the steward's phone. */
  android_id: string;
  /** Device time of the connect or disconnect, ISO 8601 UTC. */
  timestamp: string;
};