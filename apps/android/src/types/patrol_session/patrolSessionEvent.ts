
/**
 * Body of POST /api/v2/patrol-session/start and /stop, per
 * contracts/api/v2/positioning-ingestion.
 */
export type PatrolSessionEvent = {
  android_id: string;
  timestamp: string;
};