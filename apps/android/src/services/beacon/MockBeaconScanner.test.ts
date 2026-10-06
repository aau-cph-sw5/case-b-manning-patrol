// the mock scanner, with the clock frozen and the randomized delays pinned: the sequence
// of events is what matters, not the real passage of time.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createMockBeaconScanner } from "@/services/beacon/MockBeaconScanner";
import { MOCK_BEACON_IDS, MOCK_ANDROID_ID } from "@/fixtures/mockBeacons";
import type { BeaconConnectionEvent } from "@/types/beacon";

// min and max are equal, so every cycle takes exactly this long
const HOLD_MS = 5_000;
const WALK_MS = 2_000;

function createScanner(events: BeaconConnectionEvent[]) {
  const scanner = createMockBeaconScanner({
    android_id: MOCK_ANDROID_ID,
    holdRangeMs: [HOLD_MS, HOLD_MS],
    walkRangeMs: [WALK_MS, WALK_MS],
  });
  scanner.start((event) => events.push(event));
  return scanner;
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("createMockBeaconScanner", () => {
  it("connects at once, holds, disconnects, then reaches the next beacon", () => {
    const events: BeaconConnectionEvent[] = [];
    createScanner(events);

    // the first beacon is in range the moment the scan starts
    expect(events).toHaveLength(1);
    expect(events[0]!.event).toBe("CONNECTED");

    // the connection holds...
    vi.advanceTimersByTime(HOLD_MS - 1);
    expect(events).toHaveLength(1);

    // ...then drops...
    vi.advanceTimersByTime(1);
    expect(events).toHaveLength(2);
    expect(events[1]!.event).toBe("DISCONNECTED");
    expect(events[1]!.beacon_id).toBe(events[0]!.beacon_id);

    // ...and the next beacon is reached after the walk
    vi.advanceTimersByTime(WALK_MS);
    expect(events).toHaveLength(3);
    expect(events[2]!.event).toBe("CONNECTED");
    expect(events[2]!.beacon_id).not.toBe(events[0]!.beacon_id);
  });

  it("walks through the beacon ids in order", () => {
    const events: BeaconConnectionEvent[] = [];
    createScanner(events);

    // one beacon per hold + walk cycle; the last connects one cycle before the end
    vi.advanceTimersByTime((HOLD_MS + WALK_MS) * (MOCK_BEACON_IDS.length - 1));

    const connectedIds = events
      .filter((event) => event.event === "CONNECTED")
      .map((event) => event.beacon_id);
    expect(connectedIds).toEqual([...MOCK_BEACON_IDS]);
  });

  it("stamps every event with the android id and an ISO timestamp", () => {
    const events: BeaconConnectionEvent[] = [];
    createScanner(events);

    expect(events[0]!.android_id).toBe(MOCK_ANDROID_ID);
    expect(events[0]!.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
  });

  it("reports no events after stop", () => {
    const events: BeaconConnectionEvent[] = [];
    const scanner = createScanner(events);

    scanner.stop();
    vi.advanceTimersByTime((HOLD_MS + WALK_MS) * 10);

    expect(events).toHaveLength(1);
  });
});
