/** Fixed ids that let the mock scanner and the API clients act as a fixture steward. */

/**
 * The same beacon ids the backend fixtures use (fixture-events-v1.json), so
 * the mock's events look like what the rest of the system already produces.
 */
export const MOCK_BEACON_IDS = [
  "550e8400-e29b-41d4-a716-000000000002",
  "550e8400-e29b-41d4-a716-000000000003",
  "550e8400-e29b-41d4-a716-000000000004",
  "550e8400-e29b-41d4-a716-000000000050",
  "550e8400-e29b-41d4-a716-000000000060",
] as const;

/**
 * The synthetic steward the backend fixtures send events for. The real app
 * takes the device's own id; until then the mock claims to be this one.
 */
export const MOCK_ANDROID_ID = "660e8400-e29b-41d4-a716-446655440001";
