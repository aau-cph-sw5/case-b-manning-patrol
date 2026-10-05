// the backend requests for starting and stopping a steward's shift, per
// contracts/positioning-ingestion/v1. this is the only file that knows how sessions reach
// the server; useSession calls it and turns a rejection into the steward's message.
//
// each function resolves once the server has accepted the request (201) and rejects
// otherwise, including when the server cannot be reached at all.
//
// the contract's ShiftEvent carries only the device id: the startedAt stays on the phone
// (ADR-0004) and is not sent. until the real device id lands, the shift is reported for
// the synthetic steward the fixtures use.

import { MOCK_ANDROID_ID } from "@/fixtures/mockBeacons";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

async function postShiftEvent(action: "start" | "stop"): Promise<void> {
  const body = { id: MOCK_ANDROID_ID };

  // same as the connection events: the terminal shows what leaves the phone
  console.log(`POST /api/v1/shift/${action} ${JSON.stringify(body)}`);

  const response = await fetch(`${API_BASE_URL}/api/v1/shift/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`the backend rejected the shift ${action}: ${response.status}`);
  }
}

export async function startSession(): Promise<void> {
  await postShiftEvent("start");
}

export async function stopSession(): Promise<void> {
  await postShiftEvent("stop");
}
