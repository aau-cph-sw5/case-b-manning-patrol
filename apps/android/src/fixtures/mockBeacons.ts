/**
 * Mock beacon ids for the mock scanner.
 *
 * The same ids the backend fixtures use (fixture-events-v1.json), so the
 * mock's events look like what the rest of the system already produces.
 */
export const MOCK_BEACON_IDS = [
  "550e8400-e29b-41d4-a716-000000000002",
  "550e8400-e29b-41d4-a716-000000000003",
  "550e8400-e29b-41d4-a716-000000000004",
  "550e8400-e29b-41d4-a716-000000000050",
  "550e8400-e29b-41d4-a716-000000000060",
] as const;

/**
 * Mock device id: the synthetic steward the backend fixtures send events for.
 *
 * Stands in for the phone's real Android id. Every request the app sends uses
 * it until the real id is wired in.
 */
export const MOCK_ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001";
