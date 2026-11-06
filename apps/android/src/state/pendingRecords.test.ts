// pins the pending placeholder store: confirmed connects register as open
// pendings, confirmed disconnects flip them to closed (or rebuild a closed
// one from the last known connect), and a successful record fetch retires the
// pendings the server now covers.
import { afterEach, describe, expect, it } from "vitest";

import type { Record } from "@/types/patrol_records/record";
import {
  addPendingRecord,
  clearPendingRecords,
  getPendingRecords,
  markPendingClosed,
  removeReconciledPendingRecords,
} from "@/state/pendingRecords";

const BEACON_A = "550e8400-e29b-41d4-a716-00000000000a";
const BEACON_B = "550e8400-e29b-41d4-a716-00000000000b";
const START = new Date("2025-10-09T10:00:00.000Z");
const END = new Date("2025-10-09T10:05:00.000Z");

function record(beaconId: string, startedAt: Date): Record {
  return {
    androidId: "660e8400-e29b-41d4-a716-446655440001",
    beaconId,
    startedAt,
    endedAt: null,
    durationSecs: null,
    minPatrolDurationSecs: 10,
    patrolled: false,
    status: "open",
    area: {
      areaId: "area-1",
      name: "Frederiksberg platform",
      line: ["M1"],
      stationId: "station-1",
      areaType: "platform",
    },
  };
}

afterEach(() => {
  clearPendingRecords();
});

describe("addPendingRecord", () => {
  it("registers a confirmed connect as an open pending", () => {
    addPendingRecord(BEACON_A, START);

    expect(getPendingRecords()).toEqual([
      { beaconId: BEACON_A, startedAt: START, endedAt: null, status: "open", pending: true },
    ]);
  });
});

describe("markPendingClosed", () => {
  it("flips the open pending for the beacon to closed with the disconnect time", () => {
    addPendingRecord(BEACON_A, START);
    addPendingRecord(BEACON_B, START);

    markPendingClosed(BEACON_A, END);

    const pendings = getPendingRecords();
    expect(pendings.find((p) => p.beaconId === BEACON_A)).toMatchObject({
      status: "closed",
      endedAt: END,
    });
    expect(pendings.find((p) => p.beaconId === BEACON_B)).toMatchObject({ status: "open" });
  });

  it("rebuilds a closed pending from the last known connect when the connect was already reconciled", () => {
    addPendingRecord(BEACON_A, START);
    removeReconciledPendingRecords([record(BEACON_A, START)]);
    expect(getPendingRecords()).toEqual([]);

    markPendingClosed(BEACON_A, END);

    expect(getPendingRecords()).toEqual([
      { beaconId: BEACON_A, startedAt: START, endedAt: END, status: "closed", pending: true },
    ]);
  });

  it("does nothing for a beacon that was never connected", () => {
    markPendingClosed(BEACON_A, END);

    expect(getPendingRecords()).toEqual([]);
  });
});

describe("removeReconciledPendingRecords", () => {
  it("drops an open pending matched by any server record", () => {
    addPendingRecord(BEACON_A, START);

    removeReconciledPendingRecords([record(BEACON_A, START)]);

    expect(getPendingRecords()).toEqual([]);
  });

  it("drops a closed pending only when the server record is closed", () => {
    addPendingRecord(BEACON_B, START);
    markPendingClosed(BEACON_B, END);

    // server still shows the record open: the disconnect was never delivered
    removeReconciledPendingRecords([record(BEACON_B, START)]);
    expect(getPendingRecords()).toHaveLength(1);

    // once the server shows it closed, the pending is retired
    removeReconciledPendingRecords([{ ...record(BEACON_B, START), status: "closed" }]);
    expect(getPendingRecords()).toEqual([]);
  });

  it("keeps a pending whose beacon and startedAt do not match any server record", () => {
    addPendingRecord(BEACON_A, START);

    removeReconciledPendingRecords([record(BEACON_A, new Date("2025-10-09T09:00:00.000Z"))]);

    expect(getPendingRecords()).toHaveLength(1);
  });
});
