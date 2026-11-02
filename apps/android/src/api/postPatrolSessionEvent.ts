/**
 * The backend requests for starting and stopping a steward's patrol session
 * (contracts/api/v2/positioning-ingestion).
 *
 * This is the only module that knows how sessions reach the server;
 * `usePatrolSession` calls it and turns a rejection into the steward's message.
 * The body is the contract's patrol-session-event: the device id and the ISO
 * timestamp passed in. The session's `startedAt` used for the elapsed-time
 * display stays on the phone (ADR-0004). Until the real device id lands, the
 * session is reported for the synthetic steward the fixtures use.
 */
import { MOCK_ANDROID_ID } from "@/fixtures/mockBeacons";
import { PatrolSessionEvent } from "@/types/patrol_session/patrolSessionEvent";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * POST a patrol-session-event to `/api/v2/patrol-session/{action}`.
 *
 * Logs the body to the console before sending. Resolves once the server has
 * accepted the request (any 2xx; the contract answers 201) and rejects
 * otherwise, including when the server cannot be reached at all.
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
 * Report that the steward started a patrol session.
 *
 * @param timestamp - Device time of the start, ISO 8601 UTC.
 * @returns Resolves once the backend accepted it; rejects when it refuses or
 *   cannot be reached.
 */
export async function startPatrolSession(timestamp: string): Promise<void> {
  await postPatrolSessionEvent("start", timestamp);
}

/**
 * Report that the steward stopped the patrol session.
 *
 * The backend also closes every connection still open for this device, so no
 * separate disconnect needs to be sent.
 *
 * @param timestamp - Device time of the stop, ISO 8601 UTC.
 * @returns Resolves once the backend accepted it; rejects when it refuses or
 *   cannot be reached.
 */
export async function stopPatrolSession(timestamp: string): Promise<void> {
  await postPatrolSessionEvent("stop", timestamp);
}
