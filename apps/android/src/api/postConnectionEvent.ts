/**
 * Sends beacon connection events to the backend, one POST per event
 * (contracts/api/v2/positioning-ingestion).
 *
 * The endpoint says what happened, so the body carries no event field.
 */
import type { BeaconConnectionEvent } from "@/types/beacon";
import { ConnectionEvent } from "@/types/connection/connectionEvent";
import { MOCK_ANDROID_ID } from "@/fixtures/mockBeacons";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Forward one confirmed beacon connection or disconnection to the backend.
 *
 * Posts to `/api/v2/connection/connect` or `/api/v2/connection/disconnect`,
 * depending on the event kind, with the beacon id and the event's own device
 * timestamp. Every event claims to come from `MOCK_ANDROID_ID` until real
 * device ids are wired in.
 *
 * The body is logged to the console exactly as it leaves the phone: the Metro
 * terminal shows what the backend receives, which is the point of the mock
 * demo.
 *
 * @returns Resolves once the backend accepted the event; rejects on a non-2xx
 *   status or when the backend cannot be reached.
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
