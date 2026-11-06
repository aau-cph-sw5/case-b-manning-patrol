// the patrol history helpers, pinned down with fixed timestamps: the open/closed
// split, the live age of an open record, and the patrolled threshold arithmetic.
import { describe, expect, it } from "vitest";

import type { PendingRecord, Record } from "@/types/patrol_records/record";
import {
  formatDayLabel,
  formatDurationSecs,
  formatTimeOfDay,
  isPatrolled,
  mergeWithPending,
  openRecordElapsedMs,
  pendingDurationSecs,
  recordDurationSecs,
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

  it("routes pending placeholders by their own status", () => {
    const pendingOpen: PendingRecord = {
      beaconId: "550e8400-e29b-41d4-a716-00000000000a",
      startedAt: new Date(NOW - SECOND),
      endedAt: null,
      status: "open",
      pending: true,
    };
    const pendingClosed: PendingRecord = {
      ...pendingOpen,
      endedAt: new Date(NOW),
      status: "closed",
    };

    const serverOpen = record({});
    const groups = splitRecords([pendingOpen, serverOpen, pendingClosed]);

    expect(groups.open).toEqual([pendingOpen, serverOpen]);
    expect(groups.closed).toEqual([pendingClosed]);
  });
});

describe("mergeWithPending", () => {
  const pendingOpen = (beaconId: string, startedAt: Date): PendingRecord => ({
    beaconId,
    startedAt,
    endedAt: null,
    status: "open",
    pending: true,
  });

  it("prepends unreconciled pendings ahead of the server records", () => {
    const server = record({});
    const pending = pendingOpen("550e8400-e29b-41d4-a716-00000000000a", new Date(NOW - SECOND));

    expect(mergeWithPending([server], [pending])).toEqual([pending, server]);
  });

  it("drops a closed pending when the server shows the record closed", () => {
    const serverClosed = record({
      status: "closed",
      endedAt: new Date(NOW - 10 * SECOND),
      durationSecs: 20,
      patrolled: true,
    });
    const pendingClosed: PendingRecord = {
      ...pendingOpen(serverClosed.beaconId, serverClosed.startedAt),
      endedAt: new Date(NOW - 10 * SECOND),
      status: "closed",
    };

    expect(mergeWithPending([serverClosed], [pendingClosed])).toEqual([serverClosed]);
  });

  it("keeps a closed pending while the server still shows the record open, and hides the stale open record", () => {
    // the disconnect happened locally but is not delivered yet; the open
    // server record must not keep counting (and showing "Patruljeret") meanwhile
    const serverOpen = record({});
    const pendingClosed: PendingRecord = {
      ...pendingOpen(serverOpen.beaconId, serverOpen.startedAt),
      endedAt: new Date(NOW - 10 * SECOND),
      status: "closed",
    };

    const merged = mergeWithPending([serverOpen], [pendingClosed]);

    expect(merged).toEqual([pendingClosed]);
    expect(splitRecords(merged).open).toEqual([]);
    expect(splitRecords(merged).closed).toEqual([pendingClosed]);
  });

});

describe("pendingDurationSecs", () => {
  it("returns ended minus started for a closed pending, zero while open", () => {
    const closed: PendingRecord = {
      beaconId: "b",
      startedAt: new Date(NOW - 30 * SECOND),
      endedAt: new Date(NOW - 10 * SECOND),
      status: "closed",
      pending: true,
    };
    const open: PendingRecord = { ...closed, endedAt: null, status: "open" };
    expect(pendingDurationSecs(closed)).toBe(20);
    expect(pendingDurationSecs(open)).toBe(0);
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

describe("formatDayLabel", () => {
  it("formats the day with the Danish month name", () => {
    expect(formatDayLabel(new Date(2026, 9, 26))).toBe("26. oktober 2026");
    expect(formatDayLabel(new Date(2026, 0, 5))).toBe("5. januar 2026");
  });
});

describe("recordDurationSecs", () => {
  it("prefers the server's duration_secs on a closed record", () => {
    const closed = record({
      status: "closed",
      endedAt: new Date(NOW - 5 * SECOND),
      durationSecs: 720,
      patrolled: true,
    });
    expect(recordDurationSecs(closed)).toBe(720);
  });

  it("falls back to ended_at minus started_at when duration is null", () => {
    const closed = record({
      status: "closed",
      endedAt: new Date(NOW - 10 * SECOND),
      durationSecs: null,
    });
    expect(recordDurationSecs(closed)).toBe(20);
  });

  it("returns zero for an open record without a duration", () => {
    expect(recordDurationSecs(record({}))).toBe(0);
  });
});

describe("formatDurationSecs", () => {
  it("shows seconds under a minute", () => {
    expect(formatDurationSecs(0)).toBe("0 sek");
    expect(formatDurationSecs(45)).toBe("45 sek");
    expect(formatDurationSecs(59.6)).toBe("1 min");
  });

  it("shows minutes from a minute up", () => {
    expect(formatDurationSecs(60)).toBe("1 min");
    expect(formatDurationSecs(90)).toBe("2 min");
    expect(formatDurationSecs(720)).toBe("12 min");
  });

  it("clamps a negative duration to zero", () => {
    expect(formatDurationSecs(-5)).toBe("0 sek");
  });
});
