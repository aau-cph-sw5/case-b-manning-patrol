// the record-capture rules of MET-B-004 ("edge cases - business logic"). the spec is the
// skipped tests in recordCapture.test.ts: implement until each passes, unskipping one
// test at a time. pure on the event stream, so the rules can be checked without a phone.
import type { BeaconEvent } from "@/types/beacon";

export type PatrolRecord = {
  beacon_id: string;
  // the area the beacon belongs to, so station coverage and train manning come from one
  // stream (AC 7).
  area: string;
  // the first confirmed connection of the record.
  startedAt: string;
  // the last confirmed connection; null while the record is still open.
  endedAt: string | null;
};

export type RecordCaptureOptions = {
  // how long a connection must be held before a record initiates (AC 2, "x seconds").
  holdMs: number;
  // how long a connection may drop and return without breaking the record (AC 3).
  toleratedGapMs: number;
  // which area each beacon belongs to (AC 7).
  beaconAreas: Record<string, string>;
  // the session window: events outside it create nothing (AC 1). endedAt may be null for
  // an open session; a record still open at endedAt closes there, and connections that
  // never reached holdMs by then were never records (AC 5).
  session: { startedAt: string; endedAt: string | null };
};

export function computeRecords(
  events: readonly BeaconEvent[],
  options: RecordCaptureOptions,
): PatrolRecord[] {
  // TODO(MET-B-004 "edge cases - business logic"): implement per the skipped tests in
  // recordCapture.test.ts, unskipping one test at a time.
  throw new Error("not implemented: MET-B-004 record capture");
}
