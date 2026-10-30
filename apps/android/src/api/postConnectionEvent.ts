import type { BeaconConnectionEvent } from "@/types/beacon";
import { ConnectionEvent } from "@/types/connection/connectionEvent";
import { MOCK_ANDROID_ID } from "@/fixtures/mockBeacons";

/** Backend base URL from `EXPO_PUBLIC_API_URL`, defaulting to localhost:8000. */
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Send one beacon connection event to the backend.
 *
 * POSTs to `/api/v2/connection/connect` or `/api/v2/connection/disconnect`
 * per contracts/api/v2/positioning-ingestion. The endpoint says what
 * happened, so the body carries no event field. The device id is always
 * {@link MOCK_ANDROID_ID} for now.
 *
 * Logs exactly the body that leaves the phone, so the Metro terminal shows
 * what the backend receives; that is the point of the mock demo.
 *
 * @throws Error if the backend answers with a non-2xx status. Network
 * failures reject with fetch's own error.
 */
export async function postConnectionEvent(event: BeaconConnectionEvent): Promise<void> {
  try {
    const body: ConnectionEvent = {
      // For a real-device build, restore DeviceInfo.getAndroidId(); Expo Go uses the mock ID.
      android_id: MOCK_ANDROID_ID,
      beacon_id: event.beacon_id,
      timestamp: event.timestamp,
    };
    const action = event.event === "CONNECTED" ? "connect" : "disconnect";

    console.log(`POST /api/v2/connection/${action} ${JSON.stringify(body)}`);

    const response = await fetch(`${API_BASE_URL}/api/v2/connection/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`the backend rejected the ${action} event: ${response.status}`);
    }
  } catch(error) {
    throw error
  }
}
