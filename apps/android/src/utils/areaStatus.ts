// deadline arithmetic for patrol areas. everything here is pure so the sorting
// and the label formatting are testable without a device: the components only
// supply the clock.
import type { Area, AreaType, StationRecord } from "@/types/station";

// levels must be patrolled hourly, so a fresh counter starts at 60 minutes.
export const PATROL_INTERVAL_MS = 60 * 60 * 1000;

export type AreaStatus = "fresh" | "due" | "overdue";

const DUE_SOON_MS = 10 * 60 * 1000;

export function remainingMs(timeTillOverdue: number, now: number): number {
  return timeTillOverdue - now;
}

// the risk bucket that drives the cell colour. a level counts as overdue from
// the second its deadline passes, so a stale snapshot still screams red.
export function areaStatus(remaining: number): AreaStatus {
  if (remaining < 0) return "overdue";
  if (remaining <= DUE_SOON_MS) return "due";
  return "fresh";
}

// "45 min" while there is time left, "+3 min" once the deadline has passed.
// minutes round up in both directions so a counter never shows "0 min" while
// there is still time, and shows "+1 min" the moment a level slips.
export function formatCountdown(remaining: number): string {
  if (remaining > 0) return `${Math.ceil(remaining / 60_000)} min`;
  if (remaining === 0) return "0 min";
  return `+${Math.ceil(-remaining / 60_000)} min`;
}

// the area of one type a steward should look at first: the tightest uncovered
// deadline. if every level of the type is being patrolled by someone else, the
// tightest covered one is shown instead so the cell never lies by omission.
export function mostUrgentArea(
  areas: Area[],
  type: AreaType,
): Area | undefined {
  const ofType = areas.filter((area) => area.type === type);
  const pool = ofType.filter((area) => !area.coveredNow);
  const candidates = pool.length > 0 ? pool : ofType;
  if (candidates.length === 0) return undefined;
  return candidates.reduce((tightest, area) =>
    area.timeTillOverdue < tightest.timeTillOverdue ? area : tightest,
  );
}

// two numbers to compare stations by: the tightest uncovered deadline, then the
// tightest covered one. levels another steward is already patrolling never
// outrank uncovered work (AC 2), but among stations with nothing left to do the
// covered deadlines still order the list, because they matter again the moment
// the other steward leaves.
function stationUrgency(station: StationRecord, now: number): [number, number] {
  const uncovered = station.areas.filter((area) => !area.coveredNow);
  const covered = station.areas.filter((area) => area.coveredNow);
  const tightest = (areas: Area[]) =>
    areas.length === 0
      ? Number.POSITIVE_INFINITY
      : Math.min(...areas.map((area) => area.timeTillOverdue)) - now;

  return [tightest(uncovered), tightest(covered)];
}

// the steward's round in priority order (AC 1): tightest uncovered deadline
// first, covered deadlines only as a tiebreaker.
export function sortStationsByUrgency(
  stations: StationRecord[],
  now: number,
): StationRecord[] {
  return [...stations].sort((a, b) => {
    const [uncoveredA, coveredA] = stationUrgency(a, now);
    const [uncoveredB, coveredB] = stationUrgency(b, now);
    return uncoveredA - uncoveredB || coveredA - coveredB;
  });
}
