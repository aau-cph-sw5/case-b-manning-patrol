import { describe, expect, it } from "vitest";

import type { LineGroup, StationRecord } from "@/types/station";
import { stationServesLineGroup } from "@/utils/stationLineGroup";

const station = (partial: Partial<StationRecord>): StationRecord => ({
  id: "test",
  name: "Test",
  ...partial,
});

describe("stationServesLineGroup", () => {
  it("matches a group when any of the station's routes belongs to it", () => {
    const vanlose = station({ id: "vanlose", routeCodes: ["M1", "M2"] });

    expect(stationServesLineGroup(vanlose, "M1/M2")).toBe(true);
    expect(stationServesLineGroup(vanlose, "M3/M4")).toBe(false);
  });

  it("matches an interchange station in both groups", () => {
    const frederiksberg = station({ id: "frederiksberg", routeCodes: ["M1", "M2", "M3"] });

    expect(stationServesLineGroup(frederiksberg, "M1/M2")).toBe(true);
    expect(stationServesLineGroup(frederiksberg, "M3/M4")).toBe(true);
  });

  it("matches an M4 station in the M3/M4 group only", () => {
    const osterport = station({ id: "osterport", routeCodes: ["M4"] });

    expect(stationServesLineGroup(osterport, "M3/M4")).toBe(true);
    expect(stationServesLineGroup(osterport, "M1/M2")).toBe(false);
  });

  it("matches a station without route codes in no group", () => {
    const bare = station({ id: "bare", routeCodes: undefined });

    expect(stationServesLineGroup(bare, "M1/M2")).toBe(false);
    expect(stationServesLineGroup(bare, "M3/M4")).toBe(false);
  });

  it("covers both groups exhaustively", () => {
    for (const lineGroup of ["M1/M2", "M3/M4"] as LineGroup[]) {
      expect(stationServesLineGroup(station({ routeCodes: [] }), lineGroup)).toBe(false);
    }
  });
});
