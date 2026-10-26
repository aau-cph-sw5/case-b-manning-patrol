import { describe, expect, it } from "vitest";

import type { Area, LineGroup, Station } from "@/types/station";
import { stationServesLineGroup } from "@/utils/stationLineGroup";

const area = (line: string): Area => ({
  areaId: `${line.toLowerCase()}-1`,
  name: "Perron",
  line,
  areaType: "platform",
  coveredNow: false,
  overdueAt: null,
});

const station = (partial: Partial<Station>): Station => ({
  name: "Test",
  areas: [],
  ...partial,
});

describe("stationServesLineGroup", () => {
  it("matches a group when any of the station's lines belongs to it", () => {
    const vanlose = station({ name: "Vanløse", areas: [area("M1"), area("M2")] });

    expect(stationServesLineGroup(vanlose, "M1/M2")).toBe(true);
    expect(stationServesLineGroup(vanlose, "M3/M4")).toBe(false);
  });

  it("matches an interchange station in both groups", () => {
    const frederiksberg = station({
      name: "Frederiksberg",
      areas: [area("M1"), area("M2"), area("M3")],
    });

    expect(stationServesLineGroup(frederiksberg, "M1/M2")).toBe(true);
    expect(stationServesLineGroup(frederiksberg, "M3/M4")).toBe(true);
  });

  it("matches an M4 station in the M3/M4 group only", () => {
    const osterport = station({ name: "Østerport", areas: [area("M4")] });

    expect(stationServesLineGroup(osterport, "M3/M4")).toBe(true);
    expect(stationServesLineGroup(osterport, "M1/M2")).toBe(false);
  });

  it("matches a station without areas in no group", () => {
    const bare = station({ name: "Bare" });

    expect(stationServesLineGroup(bare, "M1/M2")).toBe(false);
    expect(stationServesLineGroup(bare, "M3/M4")).toBe(false);
  });

  it("covers both groups exhaustively", () => {
    for (const lineGroup of ["M1/M2", "M3/M4"] as LineGroup[]) {
      expect(stationServesLineGroup(station({ areas: [] }), lineGroup)).toBe(false);
    }
  });
});
