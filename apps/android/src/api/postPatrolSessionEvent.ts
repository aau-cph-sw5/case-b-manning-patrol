// the backend requests for starting and stopping a steward's patrol session, per
// contracts/positioning-ingestion/v2. this is the only file that knows how sessions reach
// the server; useSession calls it and turns a rejection into the steward's message.
// each function resolves once the server has accepted the request (201) and rejects
// otherwise, including when the server cannot be reached at all.
//
// the contract's PatrolSessionEvenet carries only the device id: the startedAt stays on the phone
// (ADR-0004) and is not sent. until the real device id lands, the patrol sessionis reported for
// the synthetic steward the fixtures use.
import { MOCK_ANDROID_ID } from "@/fixtures/mockBeacons";
import { PatrolSessionEvent } from "@/types/patrol_session/patrolSessionEvent";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

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

export async function startPatrolSession(timestamp: string): Promise<void> {
  await postPatrolSessionEvent("start", timestamp);
}

export async function stopPatrolSession(timestamp: string): Promise<void> {
  await postPatrolSessionEvent("stop", timestamp);
}
