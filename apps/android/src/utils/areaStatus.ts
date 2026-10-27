// deadline arithmetic for patrol areas. everything here is pure so the sorting
// and the label formatting are testable without a device: the components only
// supply the clock.
import type { Area, AreaType, Station } from "@/types/station";

// levels must be patrolled hourly, so a fresh counter starts at 60 minutes.
export const PATROL_INTERVAL_MS = 60 * 60 * 1000;

export type AreaStatus = "fresh" | "due" | "overdue";

const DUE_SOON_MS = 10 * 60 * 1000;

// a level with no deadline yet never counts down and never turns red; it
// sorts behind everything that does have one.
const NO_DEADLINE = Number.POSITIVE_INFINITY;

export function remainingMs(overdueAt: Date | null, now: number): number {
  if (overdueAt === null) return NO_DEADLINE;
  return overdueAt.getTime() - now;
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

// the deadline of one area as a plain number the arithmetic above can compare.
function deadlineOf(area: Area): number {
  return area.overdueAt === null ? NO_DEADLINE : area.overdueAt.getTime();
}

// the area of one type a steward should look at first: the tightest uncovered
// deadline. if every level of the type is being patrolled by someone else, the
// tightest covered one is shown instead so the cell never lies by omission.
export function mostUrgentArea(
  areas: Area[],
  type: AreaType,
): Area | undefined {
  const ofType = areas.filter((area) => area.areaType === type);
  const pool = ofType.filter((area) => !area.coveredNow);
  const candidates = pool.length > 0 ? pool : ofType;
  if (candidates.length === 0) return undefined;
  return candidates.reduce((tightest, area) =>
    deadlineOf(area) < deadlineOf(tightest) ? area : tightest,
  );
}

// two numbers to compare stations by: the tightest uncovered deadline, then the
// tightest covered one. levels another steward is already patrolling never
// outrank uncovered work (AC 2), but among stations with nothing left to do the
// covered deadlines still order the list, because they matter again the moment
// the other steward leaves.
function stationUrgency(station: Station, now: number): [number, number] {
  const uncovered = station.areas.filter((area) => !area.coveredNow);
  const covered = station.areas.filter((area) => area.coveredNow);
  const tightest = (areas: Area[]) =>
    areas.length === 0
      ? NO_DEADLINE
      : Math.min(...areas.map(deadlineOf)) - now;

  return [tightest(uncovered), tightest(covered)];
}

// the steward's round in priority order (AC 1): tightest uncovered deadline
// first, covered deadlines only as a tiebreaker.
export function sortStationsByUrgency(
  stations: Station[],
  now: number,
): Station[] {
  return [...stations].sort((a, b) => {
    const [uncoveredA, coveredA] = stationUrgency(a, now);
    const [uncoveredB, coveredB] = stationUrgency(b, now);
    return uncoveredA - uncoveredB || coveredA - coveredB;
  });
}
