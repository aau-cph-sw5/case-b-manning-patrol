// the patrol history helpers, pinned down with fixed timestamps: the open/closed
// split, the live age of an open record, and the patrolled threshold arithmetic.
import { describe, expect, it } from "vitest";

import type { Record } from "@/types/patrol_records/record";
import {
  formatTimeOfDay,
  isPatrolled,
  openRecordElapsedMs,
  remainingToPatrolMs,
  splitRecords,
} from "@/utils/patrolRecord";

const NOW = 1_760_000_000_000;
const SECOND = 1000;

function record(overrides: Partial<Record>): Record {
  return {
    androidId: "660e8400-e29b-41d4-a716-446655440001",
    beaconId: "550e8400-e29b-41d4-a716-000000000002",
    startedAt: new Date(NOW - 30 * SECOND),
    endedAt: null,
    durationSecs: null,
    minPatrolDurationSecs: 10,
    patrolled: false,
    status: "open",
    area: {
      areaId: "platform-a",
      name: "Frederiksberg platform",
      line: ["M1", "M2"],
      stationId: "STN-001",
      areaType: "platform",
    },
    ...overrides,
  };
}

describe("splitRecords", () => {
  it("splits by status and keeps the server's order within each group", () => {
    const open1 = record({ beaconId: "550e8400-e29b-41d4-a716-000000000002" });
    const closed1 = record({
      beaconId: "550e8400-e29b-41d4-a716-000000000003",
      status: "closed",
      endedAt: new Date(NOW - 10 * SECOND),
      durationSecs: 20,
      patrolled: true,
    });
    const open2 = record({ beaconId: "550e8400-e29b-41d4-a716-000000000004" });

    const groups = splitRecords([open1, closed1, open2]);

    expect(groups.open).toEqual([open1, open2]);
    expect(groups.closed).toEqual([closed1]);
  });

  it("returns two empty groups for a steward without records", () => {
    expect(splitRecords([])).toEqual({ open: [], closed: [] });
  });
});

describe("openRecordElapsedMs", () => {
  it("returns now minus started_at", () => {
    expect(openRecordElapsedMs(record({}), NOW)).toBe(30 * SECOND);
  });

  it("clamps clock skew to zero", () => {
    expect(openRecordElapsedMs(record({}), NOW - 60 * SECOND)).toBe(0);
  });
});

describe("isPatrolled", () => {
  it("trusts the server flag on a closed record", () => {
    // even a long visit stays unpatrolled when the server says so
    const closed = record({
      status: "closed",
      endedAt: new Date(NOW - 5 * SECOND),
      durationSecs: 5 * 60,
      patrolled: false,
    });
    expect(isPatrolled(closed, NOW)).toBe(false);
    expect(isPatrolled({ ...closed, patrolled: true }, NOW)).toBe(true);
  });

  it("recomputes open records against the minimum duration", () => {
    // started 30s ago, threshold 10s: already patrolled
    expect(isPatrolled(record({}), NOW)).toBe(true);
    // started 5s ago, threshold 10s: not yet
    expect(isPatrolled(record({ startedAt: new Date(NOW - 5 * SECOND) }), NOW)).toBe(false);
    // exactly at the threshold counts as patrolled
    expect(isPatrolled(record({ startedAt: new Date(NOW - 10 * SECOND) }), NOW)).toBe(true);
  });
});

describe("remainingToPatrolMs", () => {
  it("counts down to the threshold and stays at zero past it", () => {
    expect(remainingToPatrolMs(record({ startedAt: new Date(NOW - 4 * SECOND) }), NOW)).toBe(6 * SECOND);
    expect(remainingToPatrolMs(record({ startedAt: new Date(NOW - 10 * SECOND) }), NOW)).toBe(0);
    expect(remainingToPatrolMs(record({}), NOW)).toBe(0);
  });

  it("is always zero for closed records", () => {
    const closed = record({ status: "closed", durationSecs: 3, patrolled: false });
    expect(remainingToPatrolMs(closed, NOW)).toBe(0);
  });
});

describe("formatTimeOfDay", () => {
  it("pads hours and minutes to two digits", () => {
    expect(formatTimeOfDay(new Date(2026, 8, 21, 9, 5))).toBe("09:05");
    expect(formatTimeOfDay(new Date(2026, 8, 21, 23, 59))).toBe("23:59");
  });
});
