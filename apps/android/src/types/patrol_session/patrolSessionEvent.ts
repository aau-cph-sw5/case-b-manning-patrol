/** Wire type for patrol session start and stop. */

/**
 * Body of POST /api/v2/patrol-session/start and /api/v2/patrol-session/stop,
 * the patrol-session-event schema of contracts/api/v2/positioning-ingestion.
 */
export type PatrolSessionEvent = {
  /** UUID of the steward's phone. */
  android_id: string;
  /** Device time of the start or stop, ISO 8601 UTC. */
  timestamp: string;
};