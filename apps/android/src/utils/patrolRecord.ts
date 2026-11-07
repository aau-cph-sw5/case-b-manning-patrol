// pure helpers for the patrol history view. everything takes `now` (ms epoch)
// from the caller, like areaStatus.ts: the components supply the clock via
// useNow() and the tests need no fake timers.
import type { Record } from "@/types/patrol_records/record";

export type RecordGroups = {
  open: Record[];
  closed: Record[];
};

// the contract says clients split the list into current and previous
// connections by status; the server's most-recent-first order is kept within
// each group.
export function splitRecords(records: Record[]): RecordGroups {
  const open: Record[] = [];
  const closed: Record[] = [];
  for (const record of records) {
    if (record.status === "open") {
      open.push(record);
    } else {
      closed.push(record);
    }
  }
  return { open, closed };
}

// the server sends duration_secs null while a record is open, so the client
// computes the age itself as now - started_at; clamped at zero so a clock
// change never shows a negative timer.
export function openRecordElapsedMs(record: Record, now: number): number {
  return Math.max(0, now - record.startedAt.getTime());
}

// the server's patrolled flag on a closed record is final and trusted; on an
// open record it is only true as of the response time, so recompute it live
// against the area's minimum qualifying duration (patrol-record contract).
export function isPatrolled(record: Record, now: number): boolean {
  if (record.status === "closed") return record.patrolled;
  return openRecordElapsedMs(record, now) >= record.minPatrolDurationSecs * 1000;
}

// how much longer an open visit must last to count as patrolled; zero for
// closed records and once the threshold has passed.
export function remainingToPatrolMs(record: Record, now: number): number {
  if (record.status === "closed") return 0;
  return Math.max(
    0,
    record.minPatrolDurationSecs * 1000 - openRecordElapsedMs(record, now),
  );
}

// HH:MM time of day, e.g. when a record started or ended.
export function formatTimeOfDay(date: Date): string {
  return [date.getHours(), date.getMinutes()]
    .map((part) => String(part).padStart(2, "0"))
    .join(":");
}

/** Danish month names, indexed by `Date.getMonth()`, for day labels. */
const MONTH_NAMES = [
  "januar",
  "februar",
  "marts",
  "april",
  "maj",
  "juni",
  "juli",
  "august",
  "september",
  "oktober",
  "november",
  "december",
];

/**
 * Format a date as a Danish day label, e.g. "26. oktober 2026".
 *
 * Uses the device's time zone, like {@link formatTimeOfDay}.
 */
export function formatDayLabel(date: Date): string {
  return `${date.getDate()}. ${MONTH_NAMES[date.getMonth()]} ${date.getFullYear()}`;
}

/**
 * Return how long a record lasted in whole seconds.
 *
 * Closed records carry the server's `durationSecs`; when it is missing the
 * span is computed from `endedAt - startedAt` and clamped at zero. A record
 * with neither counts as zero seconds.
 */
export function recordDurationSecs(record: Record): number {
  if (record.durationSecs !== null) return record.durationSecs;
  if (record.endedAt !== null) {
    return Math.max(0, (record.endedAt.getTime() - record.startedAt.getTime()) / 1000);
  }
  return 0;
}

/**
 * Format whole seconds as a short Danish duration: "45 sek" under a minute,
 * otherwise "12 min" rounded to the nearest minute. Negative input shows as
 * zero.
 */
export function formatDurationSecs(totalSecs: number): string {
  const secs = Math.max(0, Math.round(totalSecs));
  if (secs < 60) return `${secs} sek`;
  return `${Math.round(secs / 60)} min`;
}
