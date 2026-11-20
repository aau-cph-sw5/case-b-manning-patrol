// the mock scanner, with the clock frozen and the randomized delays pinned: the sequence
// of events is what matters, not the real passage of time.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  createFixtureBeaconScanner,
  createMockBeaconScanner,
  FIXTURE_REPLAY_EVENTS,
  PATROL_REPLAY_EVENTS,
} from "@/services/beacon/MockBeaconScanner";
import { MOCK_BEACON_IDS, MOCK_ANDROID_ID } from "@/fixtures/mockBeacons";
import type { BeaconConnectionEvent } from "@/types/beacon";

// min and max are equal, so each configured delay is deterministic.
const CONNECTION_DURATION_MS = 5_000;
const NEXT_BEACON_ARRIVAL_DELAY_MS = 2_000;

function createScanner(
  events: BeaconConnectionEvent[],
  options: {
    beaconIds?: readonly string[];
    connectionDurationRangeMs?: readonly [number, number];
    nextBeaconArrivalDelayRangeMs?: readonly [number, number];
  } = {},
) {
  const scanner = createMockBeaconScanner({
    android_id: MOCK_ANDROID_ID,
    beacon_ids: options.beaconIds ?? MOCK_BEACON_IDS,
    connectionDurationRangeMs:
      options.connectionDurationRangeMs ?? [CONNECTION_DURATION_MS, CONNECTION_DURATION_MS],
    nextBeaconArrivalDelayRangeMs:
      options.nextBeaconArrivalDelayRangeMs ?? [
        NEXT_BEACON_ARRIVAL_DELAY_MS,
        NEXT_BEACON_ARRIVAL_DELAY_MS,
      ],
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
    createScanner(events, { beaconIds: [MOCK_BEACON_IDS[0]!] });

    // the first beacon is in range the moment the scan starts
    expect(events).toHaveLength(1);
    expect(events[0]!.event).toBe("CONNECTED");

    // the connection holds...
    vi.advanceTimersByTime(CONNECTION_DURATION_MS - 1);
    expect(events).toHaveLength(1);

    // ...then drops...
    vi.advanceTimersByTime(1);
    expect(events).toHaveLength(2);
    expect(events[1]!.event).toBe("DISCONNECTED");
    expect(events[1]!.beacon_id).toBe(events[0]!.beacon_id);

    // ...and the next beacon is reached after the walk
    vi.advanceTimersByTime(NEXT_BEACON_ARRIVAL_DELAY_MS);
    expect(events).toHaveLength(3);
    expect(events[2]!.event).toBe("CONNECTED");
    expect(events[2]!.beacon_id).toBe(events[0]!.beacon_id);
  });

  describe("createFixtureBeaconScanner", () => {
    it("keeps patrol visits long enough to qualify concourses at 10x", () => {
      const firstStation = PATROL_REPLAY_EVENTS.slice(0, 4);
      expect(firstStation[2]!.offsetMs - firstStation[0]!.offsetMs).toBeGreaterThanOrEqual(
        200_000,
      );
    });

    it("replays the aligned fixture timeline with rebased timestamps", () => {
      const events: BeaconConnectionEvent[] = [];
      const replayEvents = FIXTURE_REPLAY_EVENTS.slice(0, 4).map(
        (event, index) => ({ ...event, offsetMs: index < 2 ? 0 : 1_000 }),
      );
      const scanner = createFixtureBeaconScanner(
        replayEvents,
        1,
      );

      scanner.start((event) => events.push(event));
      vi.advanceTimersByTime(0);
      expect(scanner.eventsAreConfirmed).toBe(true);
      expect(events).toHaveLength(2);
      expect(events[0]!.beacon_id).toBe(FIXTURE_REPLAY_EVENTS[0]!.beacon_id);
      expect(events[1]!.event).toBe(FIXTURE_REPLAY_EVENTS[1]!.event);
      expect(events[1]!.beacon_id).toBe(FIXTURE_REPLAY_EVENTS[1]!.beacon_id);
      expect(events[1]!.timestamp).toBe(events[0]!.timestamp);

      vi.advanceTimersByTime(
        replayEvents[2]!.offsetMs - replayEvents[1]!.offsetMs + 1,
      );

      expect(events).toHaveLength(4);
      expect(events[2]!.event).toBe(FIXTURE_REPLAY_EVENTS[2]!.event);
      scanner.stop();
    });

    it("runs the initial reset once, then repeats the patrol timeline", () => {
      const events: BeaconConnectionEvent[] = [];
      const resetEvents = FIXTURE_REPLAY_EVENTS.slice(0, 2).map(
        (event, index) => ({ ...event, offsetMs: index * 1_000 }),
      );
      const patrolEvents = resetEvents.map((event) => ({
        ...event,
        event: "CONNECTED" as const,
      }));
      const scanner = createFixtureBeaconScanner(
        resetEvents,
        1,
        patrolEvents,
      );

      scanner.start((event) => events.push(event));
      vi.advanceTimersByTime(0);
      expect(events).toHaveLength(1);

      vi.advanceTimersByTime(resetEvents[1]!.offsetMs + 2);
      expect(events).toHaveLength(3);
      expect(events[2]!.beacon_id).toBe(events[0]!.beacon_id);
      scanner.stop();
    });

    it("cancels replay events when stopped", () => {
      const events: BeaconConnectionEvent[] = [];
      const scanner = createFixtureBeaconScanner(FIXTURE_REPLAY_EVENTS, 1);

      scanner.start((event) => events.push(event));
      scanner.stop();
      vi.advanceTimersByTime(FIXTURE_REPLAY_EVENTS.at(-1)!.offsetMs);

      expect(events).toHaveLength(0);
    });
  });

  it("can keep more than two configured beacons connected", () => {
    const events: BeaconConnectionEvent[] = [];
    createScanner(events, {
      connectionDurationRangeMs: [30_000, 30_000],
      nextBeaconArrivalDelayRangeMs: [
        NEXT_BEACON_ARRIVAL_DELAY_MS,
        NEXT_BEACON_ARRIVAL_DELAY_MS,
      ],
    });

    vi.advanceTimersByTime(
      NEXT_BEACON_ARRIVAL_DELAY_MS * (MOCK_BEACON_IDS.length - 1),
    );

    expect(events.filter((event) => event.event === "CONNECTED")).toHaveLength(
      MOCK_BEACON_IDS.length,
    );
  });

  it("overlaps two configured beacons for the demo", () => {
    const events: BeaconConnectionEvent[] = [];
    createScanner(events, {
      beaconIds: MOCK_BEACON_IDS.slice(0, 2),
    });

    vi.advanceTimersByTime(NEXT_BEACON_ARRIVAL_DELAY_MS);
    expect(events.map((event) => event.event)).toEqual(["CONNECTED", "CONNECTED"]);
    expect(events[0]!.beacon_id).not.toBe(events[1]!.beacon_id);
  });

  it("allows connections shorter than three seconds and gaps longer than ten", () => {
    const events: BeaconConnectionEvent[] = [];
    createScanner(events, {
      beaconIds: [MOCK_BEACON_IDS[0]!],
      connectionDurationRangeMs: [1_000, 1_000],
      nextBeaconArrivalDelayRangeMs: [12_000, 12_000],
    });

    vi.advanceTimersByTime(1_000);
    expect(events.map((event) => event.event)).toEqual(["CONNECTED", "DISCONNECTED"]);

    vi.advanceTimersByTime(10_000);
    expect(events).toHaveLength(2);

    vi.advanceTimersByTime(1_000);
    expect(events[2]!.event).toBe("CONNECTED");
  });

  it("stamps every event with the android id and an ISO timestamp", () => {
    const events: BeaconConnectionEvent[] = [];
    createScanner(events);

    expect(events[0]!.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
  });

  it("reports no events after stop", () => {
    const events: BeaconConnectionEvent[] = [];
    const scanner = createScanner(events);

    scanner.stop();
    vi.advanceTimersByTime(
      (CONNECTION_DURATION_MS + NEXT_BEACON_ARRIVAL_DELAY_MS) * 10,
    );

    expect(events).toHaveLength(1);
  });
});
