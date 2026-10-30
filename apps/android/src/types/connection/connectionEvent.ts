/**
 * Body of POST /api/v2/connection/connect and /disconnect, per
 * contracts/api/v2/positioning-ingestion.
 */
export type ConnectionEvent = {
  beacon_id: string;
  android_id: string;
  timestamp: string;
};