/**
 * Backend requests for starting and stopping a steward's patrol session, per
 * contracts/api/v2/positioning-ingestion.
 *
 * This is the only file that knows how sessions reach the server;
 * usePatrolSession calls it and turns a rejection into the steward's message.
 */
import { MOCK_ANDROID_ID } from "@/fixtures/mockBeacons";
import { PatrolSessionEvent } from "@/types/patrol_session/patrolSessionEvent";

/** Backend base URL from `EXPO_PUBLIC_API_URL`, defaulting to localhost:8000. */
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * POST a session start or stop to `/api/v2/patrol-session/{action}`.
 *
 * The body is the device id and the given timestamp. The phone is the source
 * of truth for event time (ADR-0004). Until the real device id lands, the
 * session is reported for the synthetic steward the fixtures use
 * ({@link MOCK_ANDROID_ID}). Logs the body before sending.
 *
 * @param timestamp - Device time as an ISO 8601 string.
 * @throws Error if the backend answers with a non-2xx status. Network
 * failures reject with fetch's own error.
 */
async function postPatrolSessionEvent(action: "start" | "stop", timestamp: string): Promise<void> {

  try {
    const body: PatrolSessionEvent = {
      // For a real-device build, restore DeviceInfo.getAndroidId(); Expo Go uses the mock ID.
      android_id: MOCK_ANDROID_ID,
      timestamp: timestamp
    };

    console.log(`POST /api/v2/patrol-session/${action} ${JSON.stringify(body)}`);

    const response = await fetch(
      `${API_BASE_URL}/api/v2/patrol-session/${action}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!response.ok) {
      throw new Error(
        `the backend rejected the patrol session ${action}: ${response.status}`,
      );
    }
  } catch (error) {
    throw error;
  }
}

/**
 * Tell the backend the steward started a patrol session.
 *
 * Resolves once the server has accepted the request. Rejects on a non-2xx
 * status or when the server cannot be reached at all.
 *
 * @param timestamp - Device time of the start as an ISO 8601 string.
 */
export async function startPatrolSession(timestamp: string): Promise<void> {
  await postPatrolSessionEvent("start", timestamp);
}

/**
 * Tell the backend the steward stopped the patrol session.
 *
 * Resolves once the server has accepted the request. Rejects on a non-2xx
 * status or when the server cannot be reached at all.
 *
 * @param timestamp - Device time of the stop as an ISO 8601 string.
 */
export async function stopPatrolSession(timestamp: string): Promise<void> {
  await postPatrolSessionEvent("stop", timestamp);
}
