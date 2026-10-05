// sends beacon connection events to the backend, one POST per event per
// contracts/positioning-ingestion/v1: the endpoint says what happened, so the body
// carries no event field.
//
// the console.log prints exactly the body that leaves the phone: the metro terminal
// shows what the backend receives, which is the point of the mock demo.
import type { BeaconEvent } from "@/types/beacon";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

export async function postConnectionEvent(event: BeaconEvent): Promise<void> {
  const body = {
    android_id: event.android_id,
    beacon_id: event.beacon_id,
    timestamp: event.timestamp,
  };
  const action = event.event === "CONNECTED" ? "connect" : "disconnect";

  console.log(`POST /api/v1/connection/${action} ${JSON.stringify(body)}`);

  const response = await fetch(`${API_BASE_URL}/api/v1/connection/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`the backend rejected the ${action} event: ${response.status}`);
  }
}
