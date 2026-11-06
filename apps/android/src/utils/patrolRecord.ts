// pure helpers for the patrol history view. everything takes `now` (ms epoch)
// from the caller, like areaStatus.ts: the components supply the clock via
// useNow() and the tests need no fake timers.
import type { HistoryEntry, PendingRecord, Record } from "@/types/patrol_records/record";

export type RecordGroups = {
  open: HistoryEntry[];
  closed: HistoryEntry[];
};

// the contract says clients split the list into current and previous
// connections by status; the server's most-recent-first order is kept within
// each group, and pendings keep their own insertion order.
export function splitRecords(entries: HistoryEntry[]): RecordGroups {
  const open: HistoryEntry[] = [];
  const closed: HistoryEntry[] = [];
  for (const entry of entries) {
    if (entry.status === "open") {
      open.push(entry);
    } else {
      closed.push(entry);
    }
  }
  return { open, closed };
}

// a pending and its server record describe the same connection when the beacon
// and the connect timestamp match; the server stamps started_at from the
// connect event's own device timestamp, so the two agree exactly.
export function sameConnection(
  a: { beaconId: string; startedAt: Date },
  b: { beaconId: string; startedAt: Date },
): boolean {
  return a.beaconId === b.beaconId && a.startedAt.getTime() === b.startedAt.getTime();
}

/**
 * Return whether a fetched server record retires a pending placeholder.
 *
 * Any matching record retires an open pending. A closed pending is retired
 * only by a matching closed record: a still-open server record means the
 * disconnect was never delivered, so the pending stays until the retry sends
 * it and a later fetch shows the record closed.
 */
export function isReconciledBy(record: Record, pending: PendingRecord): boolean {
  return sameConnection(record, pending) && (pending.status === "open" || record.status === "closed");
}

/**
 * Merge fetched server records with client-side pendings, most recent first.
 *
 * A pending whose connection the server has registered (see
 * {@link isReconciledBy}) is dropped — the server record wins and brings the
 * resolved area. A closed pending also supersedes a matching still-open server
 * record, so a locally ended connection stops its open timer immediately. The
 * rest of the pendings are prepended, since an unacknowledged connection is
 * newer than anything the server sent.
 */
export function mergeWithPending(records: Record[], pending: PendingRecord[]): HistoryEntry[] {
  const unreconciled = pending.filter(
    (entry) => !records.some((record) => isReconciledBy(record, entry)),
  );
  // a closed pending supersedes a matching still-open server record: the local
  // disconnect is newer truth, and the open record would keep counting (and
  // possibly show "Patruljeret") for a connection that has already ended
  const closedPendingKeys = new Set(
    pending
      .filter((entry) => entry.status === "closed")
      .map((entry) => `${entry.beaconId}-${entry.startedAt.getTime()}`),
  );
  const visibleRecords = records.filter(
    (record) =>
      record.status !== "open" ||
      !closedPendingKeys.has(`${record.beaconId}-${record.startedAt.getTime()}`),
  );
  return [...unreconciled, ...visibleRecords];
}

// the server sends duration_secs null while a record is open, so the client
// computes the age itself as now - started_at; clamped at zero so a clock
// change never shows a negative timer.
export function openRecordElapsedMs(record: { startedAt: Date }, now: number): number {
  return Math.max(0, now - record.startedAt.getTime());
}

/** Return how long a closed pending lasted, computed from its own timestamps. */
export function pendingDurationSecs(pending: PendingRecord): number {
  if (pending.endedAt === null) return 0;
  return Math.max(0, (pending.endedAt.getTime() - pending.startedAt.getTime()) / 1000);
}

/** Return the first 8 characters of a beacon id, for pending cards without an area name. */
export function shortBeaconId(beaconId: string): string {
  return beaconId.slice(0, 8);
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
