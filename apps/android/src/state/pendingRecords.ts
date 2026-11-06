/**
 * Client-side placeholders for beacon connections the backend has not
 * acknowledged yet (patrol-record contract: while a connect/disconnect POST
 * is in flight or has failed, the phone's local state is the source of
 * origin).
 *
 * Plain module state with no subscription on purpose: the scanner fires from
 * timer callbacks outside React, and the history screen already re-renders
 * every second via useNow and re-reads {@link getPendingRecords} in its
 * merge, so a pending shows up there within one tick. A pending is retired
 * only when a successful GET /api/v2/record contains the matching record —
 * never on a POST acknowledgement — via {@link removeReconciledPendingRecords}.
 */
import type { PendingRecord, Record } from "@/types/patrol_records/record";
import { isReconciledBy } from "@/utils/patrolRecord";

// keyed by beaconId + startedAt so a quick reconnect to the same beacon does
// not clobber the earlier pending
const pendingByKey = new Map<string, PendingRecord>();
// last confirmed connect per beacon, so a disconnect can still be turned into
// a closed pending after a fetch already reconciled the connect
const lastConnectAt = new Map<string, Date>();

/** Build the map key that ties a pending to its future server record. */
function key(beaconId: string, startedAt: Date): string {
  return `${beaconId}-${startedAt.getTime()}`;
}

/**
 * Register a confirmed connect as an open pending record.
 *
 * Call this before the connect POST leaves the phone; a failed POST then
 * leaves the pending in place, which is the offline behavior we want.
 */
export function addPendingRecord(beaconId: string, startedAt: Date): void {
  lastConnectAt.set(beaconId, startedAt);
  pendingByKey.set(key(beaconId, startedAt), {
    beaconId,
    startedAt,
    endedAt: null,
    status: "open",
    pending: true,
  });
}

/**
 * Flip the open pending for a beacon to closed, or rebuild one as closed when
 * a fetch already reconciled the connect. Does nothing for an unknown beacon.
 *
 * Called when the disconnect is confirmed (the POST leaves the phone), so the
 * close is final; it also confirms a provisional close from the raw event.
 */
export function markPendingClosed(beaconId: string, endedAt: Date): void {
  for (const pending of pendingByKey.values()) {
    if (pending.beaconId === beaconId && pending.status === "open") {
      pendingByKey.set(key(pending.beaconId, pending.startedAt), {
        ...pending,
        status: "closed",
        endedAt,
        provisional: undefined,
      });
      return;
    }
    if (pending.beaconId === beaconId && pending.status === "closed") {
      // already provisionally closed by the raw disconnect: confirm it
      pendingByKey.set(key(pending.beaconId, pending.startedAt), {
        ...pending,
        endedAt,
        provisional: undefined,
      });
      return;
    }
  }
  const startedAt = lastConnectAt.get(beaconId);
  if (startedAt !== undefined) {
    pendingByKey.set(key(beaconId, startedAt), {
      beaconId,
      startedAt,
      endedAt,
      status: "closed",
      pending: true,
    });
  }
}

/**
 * Provisionally close the pending for a beacon on the raw scanner disconnect,
 * so the history stops the open timer at the actual disconnect instead of
 * after the confirmation delay.
 *
 * Flips an existing open pending, or rebuilds a provisional closed one from
 * the last confirmed connect when a fetch already reconciled the pending (the
 * server record is still open, so the store no longer holds it). Only applies
 * to a qualified connection — a disconnect of an unqualified one has no
 * remembered connect and is dropped silently, like the BeaconEventService
 * drops it.
 */
export function markPendingDisconnected(beaconId: string, endedAt: Date): void {
  for (const pending of pendingByKey.values()) {
    if (pending.beaconId === beaconId && pending.status === "open") {
      pendingByKey.set(key(pending.beaconId, pending.startedAt), {
        ...pending,
        status: "closed",
        endedAt,
        provisional: true,
      });
      return;
    }
  }
  const startedAt = lastConnectAt.get(beaconId);
  if (startedAt !== undefined) {
    pendingByKey.set(key(beaconId, startedAt), {
      beaconId,
      startedAt,
      endedAt,
      status: "closed",
      provisional: true,
      pending: true,
    });
  }
}

/**
 * Re-open a provisionally closed pending when its beacon reconnects before the
 * disconnect was confirmed — the BeaconEventService cancels the disconnect in
 * the same situation. A confirmed close is final and is not re-opened.
 */
export function reopenProvisionalPending(beaconId: string): void {
  for (const pending of pendingByKey.values()) {
    if (pending.beaconId !== beaconId || pending.status !== "closed") continue;
    if (pending.provisional !== true) continue;
    pendingByKey.set(key(pending.beaconId, pending.startedAt), {
      ...pending,
      status: "open",
      endedAt: null,
      provisional: undefined,
    });
    return;
  }
}

/** Return every pending placeholder, oldest connect first. */
export function getPendingRecords(): PendingRecord[] {
  return [...pendingByKey.values()];
}

/**
 * Drop every pending that a fetched server record now covers, matched on
 * beaconId + startedAt. An open pending is retired by any matching record; a
 * closed pending only by a matching *closed* record — a still-open server
 * record means the disconnect was never delivered, so the pending must stay
 * for the retry to send it. Call after a successful fetch so the module state
 * does not grow for the whole shift.
 */
export function removeReconciledPendingRecords(records: Record[]): void {
  for (const pending of [...pendingByKey.values()]) {
    if (records.some((record) => isReconciledBy(record, pending))) {
      pendingByKey.delete(key(pending.beaconId, pending.startedAt));
    }
  }
}

/** Forget all pendings and remembered connects. Used by tests. */
export function clearPendingRecords(): void {
  pendingByKey.clear();
  lastConnectAt.clear();
}
