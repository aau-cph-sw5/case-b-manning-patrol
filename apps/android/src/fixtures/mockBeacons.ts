/** Fixed ids that let the mock scanner and the API clients act as a fixture steward. */

/** Beacon ids used by the station records in the backend reference data. */
const REFERENCE_STATION_INDICES = Array.from({ length: 42 }, (_, index) => index + 1)
  .filter((index) => index !== 6);

export const MOCK_BEACON_IDS = REFERENCE_STATION_INDICES.map((index) =>
  `660e8400-e29b-41d4-a716-446655440${index.toString(16).padStart(3, "0")}`,
);

/** Concourse beacon paired with each station beacon. */
export const MOCK_CONCOURSE_BEACON_IDS = REFERENCE_STATION_INDICES.map((index) =>
  `660e8400-e29b-41d4-a716-446655440${(0x80 + index).toString(16).padStart(3, "0")}`,
);

/**
 * The synthetic steward the backend fixtures send events for. The real app
 * takes the device's own id; until then the mock claims to be this one.
 */
export const MOCK_ANDROID_ID = "660e8400-e29b-41d4-a716-446655440000";
