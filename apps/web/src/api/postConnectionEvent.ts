// sends beacon connection events to the backend, one POST per event per
// contracts/positioning-ingestion/v2: the endpoint says what happened, so the body
// carries no event field.
//
// the console.log prints exactly the body that leaves the browser: the server log
// shows what the backend receives.

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type BeaconEventKind = "CONNECTED" | "DISCONNECTED";

export type BeaconConnectionEvent = {
  event: BeaconEventKind;
  beacon_id: string;
  // device time as ISO 8601 UTC with milliseconds, e.g. "2026-05-30T03:08:13.000Z".
  // the browser is the source of truth for event time (ADR-0004).
  timestamp: string;
};

export type ConnectionEvent = {
  beacon_id: string;
  android_id: string;
  timestamp: string;
};

// For a real-device build, restore actual device ID; Vite uses the mock ID.
export const MOCK_DEVICE_ID = "660e8400-e29b-41d4-a716-446655440001";

export async function postConnectionEvent(event: BeaconConnectionEvent): Promise<void> {
  try {
    const body: ConnectionEvent = {
      android_id: MOCK_DEVICE_ID,
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
  } catch (error) {
    throw error;
  }
}
