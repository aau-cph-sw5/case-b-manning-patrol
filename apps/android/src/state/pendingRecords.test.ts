// pins the pending placeholder store: confirmed connects register as open
// pendings, disconnects close them (provisionally on the raw event, finally on
// the confirmed one, re-opened if the beacon reconnects in between), and a
// successful record fetch retires the pendings the server now covers.
import { afterEach, describe, expect, it } from "vitest";

import type { Record } from "@/types/patrol_records/record";
import {
  addPendingRecord,
  clearPendingRecords,
  getPendingRecords,
  markPendingClosed,
  markPendingDisconnected,
  removeReconciledPendingRecords,
  reopenProvisionalPending,
} from "@/state/pendingRecords";

const BEACON_A = "550e8400-e29b-41d4-a716-00000000000a";
const BEACON_B = "550e8400-e29b-41d4-a716-00000000000b";
const START = new Date("2025-10-09T10:00:00.000Z");
const END = new Date("2025-10-09T10:05:00.000Z");

function record(beaconId: string, startedAt: Date, status: Record["status"] = "open"): Record {
  return {
    androidId: "660e8400-e29b-41d4-a716-446655440001",
    beaconId,
    startedAt,
    endedAt: null,
    durationSecs: null,
    minPatrolDurationSecs: 10,
    patrolled: false,
    status,
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

describe("addPendingRecord / markPendingClosed", () => {
  it("registers a confirmed connect as open and flips it to closed on confirmed disconnect", () => {
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

  it("rebuilds a closed pending from the last known connect when a fetch already reconciled it", () => {
    addPendingRecord(BEACON_A, START);
    removeReconciledPendingRecords([record(BEACON_A, START)]);

    markPendingClosed(BEACON_A, END);

    expect(getPendingRecords()).toEqual([
      { beaconId: BEACON_A, startedAt: START, endedAt: END, status: "closed", pending: true },
    ]);
  });
});

describe("provisional close on raw disconnect", () => {
  it("closes the open pending immediately, re-opens on reconnect, and confirms on the confirmed disconnect", () => {
    addPendingRecord(BEACON_A, START);

    markPendingDisconnected(BEACON_A, END);
    expect(getPendingRecords()[0]).toMatchObject({ status: "closed", endedAt: END, provisional: true });

    reopenProvisionalPending(BEACON_A);
    expect(getPendingRecords()[0]).toMatchObject({ status: "open", endedAt: null, provisional: undefined });

    markPendingDisconnected(BEACON_A, END);
    markPendingClosed(BEACON_A, END);
    expect(getPendingRecords()[0]).toMatchObject({ status: "closed", endedAt: END, provisional: undefined });
  });

  it("rebuilds a provisional close from the last confirmed connect when the pending was reconciled", () => {
    addPendingRecord(BEACON_A, START);
    removeReconciledPendingRecords([record(BEACON_A, START)]);

    markPendingDisconnected(BEACON_A, END);

    expect(getPendingRecords()).toEqual([
      { beaconId: BEACON_A, startedAt: START, endedAt: END, status: "closed", provisional: true, pending: true },
    ]);
  });

});

describe("removeReconciledPendingRecords", () => {
  it("drops an open pending on any matching server record, but a closed pending only on a closed one", () => {
    addPendingRecord(BEACON_A, START);
    addPendingRecord(BEACON_B, START);
    markPendingClosed(BEACON_B, END);

    removeReconciledPendingRecords([
      record(BEACON_A, START),
      record(BEACON_B, START), // still open server-side: disconnect not delivered
    ]);
    expect(getPendingRecords().map((p) => p.beaconId)).toEqual([BEACON_B]);

    removeReconciledPendingRecords([record(BEACON_B, START, "closed")]);
    expect(getPendingRecords()).toEqual([]);
  });
});
