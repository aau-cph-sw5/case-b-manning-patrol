// the deadline rules the steward's screen is built on: the countdown text, the
// risk buckets, and the priority order. all inputs are fixed timestamps so the
// arithmetic is pinned down exactly.
import { describe, expect, it } from "vitest";

import type { Area, Station } from "@/types/station";
import {
  areaStatus,
  formatCountdown,
  mostUrgentArea,
  remainingMs,
  sortStationsByUrgency,
} from "@/utils/areaStatus";

const NOW = 1760000000000;
const MINUTE = 60_000;

function area(overrides: Partial<Area>): Area {
  return {
    areaId: "platform-1",
    name: "Perron",
    line: ["M1"],
    areaType: "platform",
    coveredNow: false,
    overdueAt: new Date(NOW + 45 * MINUTE),
    ...overrides,
  };
}

function station(name: string, areas: Area[]): Station {
  return { name, areas };
}

describe("formatCountdown", () => {
  it("counts down in minutes, rounding up", () => {
    expect(formatCountdown(45 * MINUTE)).toBe("45 min");
    expect(formatCountdown(60 * MINUTE)).toBe("60 min");
    expect(formatCountdown(59_000)).toBe("1 min");
    expect(formatCountdown(1)).toBe("1 min");
  });

  it("hits 0 exactly at the deadline and counts up past it", () => {
    expect(formatCountdown(0)).toBe("0 min");
    expect(formatCountdown(-1)).toBe("+1 min");
    expect(formatCountdown(-30_000)).toBe("+1 min");
    expect(formatCountdown(-61_000)).toBe("+2 min");
  });
});

describe("areaStatus", () => {
  it("marks a level overdue from the second its deadline passes", () => {
    expect(areaStatus(-1)).toBe("overdue");
    expect(areaStatus(0)).toBe("due");
  });

  it("marks the last ten minutes as due and the rest as fresh", () => {
    expect(areaStatus(10 * MINUTE)).toBe("due");
    expect(areaStatus(10 * MINUTE + 1)).toBe("fresh");
  });
});

describe("remainingMs", () => {
  it("is the distance from now to the deadline, negative once overdue", () => {
    expect(remainingMs(new Date(NOW + 5 * MINUTE), NOW)).toBe(5 * MINUTE);
    expect(remainingMs(new Date(NOW - 5 * MINUTE), NOW)).toBe(-5 * MINUTE);
  });

  it("treats a level with no deadline yet as never due", () => {
    expect(remainingMs(null, NOW)).toBe(Number.POSITIVE_INFINITY);
  });
});

describe("mostUrgentArea", () => {
  it("picks the tightest deadline of the type", () => {
    const late = area({ name: "Late platform", overdueAt: new Date(NOW + 2 * MINUTE) });
    const soon = area({ name: "Soon platform", overdueAt: new Date(NOW + 5 * MINUTE) });
    const concourse = area({ areaType: "concourse", overdueAt: new Date(NOW) });

    expect(mostUrgentArea([late, soon, concourse], "platform")).toBe(late);
    expect(mostUrgentArea([late, soon, concourse], "concourse")).toBe(concourse);
  });

  it("prefers an uncovered level over a tighter covered one", () => {
    const covered = area({ name: "Covered", overdueAt: new Date(NOW), coveredNow: true });
    const uncovered = area({ name: "Uncovered", overdueAt: new Date(NOW + 20 * MINUTE) });

    expect(mostUrgentArea([covered, uncovered], "platform")).toBe(uncovered);
  });

  it("falls back to the covered level when nothing else is there", () => {
    const covered = area({ coveredNow: true });
    expect(mostUrgentArea([covered], "platform")).toBe(covered);
  });

  it("sorts a level with no deadline behind one that has a deadline", () => {
    const undated = area({ name: "Undated", overdueAt: null });
    const dated = area({ name: "Dated", overdueAt: new Date(NOW + 20 * MINUTE) });

    expect(mostUrgentArea([undated, dated], "platform")).toBe(dated);
  });

  it("returns undefined when the station has no level of the type", () => {
    const concourse = area({ areaType: "concourse" });
    expect(mostUrgentArea([concourse], "platform")).toBeUndefined();
  });
});

describe("sortStationsByUrgency", () => {
  it("puts the station with the tightest uncovered deadline first", () => {
    const relaxed = station("Relaxed", [
      area({ overdueAt: new Date(NOW + 50 * MINUTE) }),
    ]);
    const urgent = station("Urgent", [
      area({ overdueAt: new Date(NOW + 5 * MINUTE) }),
    ]);
    const overdue = station("Overdue", [
      area({ overdueAt: new Date(NOW - 3 * MINUTE) }),
    ]);

    expect(sortStationsByUrgency([relaxed, overdue, urgent], NOW)).toEqual([
      overdue,
      urgent,
      relaxed,
    ]);
  });

  it("sorts a station whose levels are all covered behind uncovered work", () => {
    const coveredOnly = station("Covered only", [
      area({ overdueAt: new Date(NOW), coveredNow: true }),
    ]);
    const uncovered = station("Uncovered", [
      area({ overdueAt: new Date(NOW + 40 * MINUTE) }),
    ]);

    expect(sortStationsByUrgency([coveredOnly, uncovered], NOW)).toEqual([
      uncovered,
      coveredOnly,
    ]);
  });

  it("keeps stations with no areas at the end", () => {
    const empty = station("Empty", []);
    const hasWork = station("Has work", [area({})]);

    expect(sortStationsByUrgency([empty, hasWork], NOW)).toEqual([
      hasWork,
      empty,
    ]);
  });

  it("keeps a station with no deadlines yet behind stations with work", () => {
    const undated = station("Undated", [area({ overdueAt: null })]);
    const hasWork = station("Has work", [area({})]);

    expect(sortStationsByUrgency([undated, hasWork], NOW)).toEqual([
      hasWork,
      undated,
    ]);
  });
});
