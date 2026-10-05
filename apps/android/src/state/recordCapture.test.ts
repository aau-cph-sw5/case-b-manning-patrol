// TDD specs for the record capture of MET-B-004 ("edge cases - business logic"): each test
// is one acceptance criterion, written before the implementation. they are skipped so ci
// stays green; the workflow is: unskip one test, implement until it passes, repeat.
import { describe, expect, it } from "vitest";

import { computeRecords, type RecordCaptureOptions } from "@/state/recordCapture";
import type { BeaconEvent, BeaconEventKind } from "@/types/beacon";

const T0 = "2026-05-30T03:08:00.000Z";
const at = (ms: number) => new Date(Date.parse(T0) + ms).toISOString();

const event = (
  kind: BeaconEventKind,
  beacon_id: string,
  timestamp: string,
): BeaconEvent => ({ event: kind, beacon_id, android_id: "steward-1", timestamp });

const options = (overrides: Partial<RecordCaptureOptions> = {}): RecordCaptureOptions => ({
  holdMs: 10_000,
  toleratedGapMs: 5_000,
  beaconAreas: {
    "beacon-1": "kongens-nytorv platform",
    "beacon-2": "kongens-nytorv concourse",
  },
  session: { startedAt: T0, endedAt: null },
  ...overrides,
});

describe("record capture (MET-B-004 acceptance criteria)", () => {
  it.skip("a beacon connection outside an active session creates nothing (AC 1)", () => {
    const records = computeRecords(
      [
        event("CONNECTED", "beacon-1", at(-60_000)),
        event("DISCONNECTED", "beacon-1", at(-30_000)),
      ],
      options({ session: { startedAt: T0, endedAt: at(120_000) } }),
    );
    expect(records).toEqual([]);
  });

  it.skip("a record initiates once a beacon has been connected for x seconds (AC 2)", () => {
    const records = computeRecords(
      [
        event("CONNECTED", "beacon-1", at(0)),
        event("DISCONNECTED", "beacon-1", at(15_000)),
      ],
      options(),
    );
    expect(records).toEqual([
      {
        beacon_id: "beacon-1",
        area: "kongens-nytorv platform",
        startedAt: at(0),
        endedAt: at(15_000),
      },
    ]);
  });

  it.skip("a connection that never reaches x seconds is discarded (AC 2)", () => {
    const records = computeRecords(
      [
        event("CONNECTED", "beacon-1", at(0)),
        event("DISCONNECTED", "beacon-1", at(5_000)),
      ],
      options(),
    );
    expect(records).toEqual([]);
  });

  it.skip("a disconnect that returns within the tolerated gap continues the same record (AC 3)", () => {
    const records = computeRecords(
      [
        event("CONNECTED", "beacon-1", at(0)),
        event("DISCONNECTED", "beacon-1", at(10_000)),
        // 2s gap, inside the tolerated 5s
        event("CONNECTED", "beacon-1", at(12_000)),
        event("DISCONNECTED", "beacon-1", at(25_000)),
      ],
      options(),
    );
    expect(records).toEqual([
      {
        beacon_id: "beacon-1",
        area: "kongens-nytorv platform",
        startedAt: at(0),
        endedAt: at(25_000),
      },
    ]);
  });

  it.skip("a record closes when the connection is lost longer than the tolerated gap, at its last confirmed connection (AC 4)", () => {
    const records = computeRecords(
      [
        event("CONNECTED", "beacon-1", at(0)),
        event("DISCONNECTED", "beacon-1", at(10_000)),
        // 10s gap, outside the tolerated 5s: a second record opens
        event("CONNECTED", "beacon-1", at(20_000)),
        event("DISCONNECTED", "beacon-1", at(35_000)),
      ],
      options(),
    );
    expect(records).toEqual([
      {
        beacon_id: "beacon-1",
        area: "kongens-nytorv platform",
        startedAt: at(0),
        endedAt: at(10_000),
      },
      {
        beacon_id: "beacon-1",
        area: "kongens-nytorv platform",
        startedAt: at(20_000),
        endedAt: at(35_000),
      },
    ]);
  });

  it.skip("stop closes every open record; connections shorter than x seconds were never records (AC 5)", () => {
    const records = computeRecords(
      [
        // connected from the start of the session until it ends: a record
        event("CONNECTED", "beacon-1", at(0)),
        // connected for only 5s before the session ends: discarded
        event("CONNECTED", "beacon-2", at(35_000)),
      ],
      options({ session: { startedAt: T0, endedAt: at(40_000) } }),
    );
    expect(records).toEqual([
      {
        beacon_id: "beacon-1",
        area: "kongens-nytorv platform",
        startedAt: at(0),
        endedAt: at(40_000),
      },
    ]);
  });

  it.skip("records for more than one area can be open at the same time (AC 6, AC 7)", () => {
    const records = computeRecords(
      [
        event("CONNECTED", "beacon-1", at(0)),
        event("CONNECTED", "beacon-2", at(1_000)),
        event("DISCONNECTED", "beacon-1", at(12_000)),
        event("DISCONNECTED", "beacon-2", at(20_000)),
      ],
      options(),
    );
    expect(records).toEqual([
      {
        beacon_id: "beacon-1",
        area: "kongens-nytorv platform",
        startedAt: at(0),
        endedAt: at(12_000),
      },
      {
        beacon_id: "beacon-2",
        area: "kongens-nytorv concourse",
        startedAt: at(1_000),
        endedAt: at(20_000),
      },
    ]);
  });
});
