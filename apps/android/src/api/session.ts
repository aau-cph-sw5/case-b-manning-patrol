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

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

async function postPatrolSessionEvent(action: "start" | "stop"): Promise<void> {
  const body = { id: MOCK_ANDROID_ID };

  // same as the connection events: the terminal shows what leaves the phone
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
}

export async function startPatrolSession(): Promise<void> {
  await postPatrolSessionEvent("start");
}

export async function stopPatrolSession(): Promise<void> {
  await postPatrolSessionEvent("stop");
}
