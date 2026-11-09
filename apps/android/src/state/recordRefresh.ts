/**
 * A version counter for "the backend's record list may have changed".
 *
 * Bumped when an ingestion POST is acknowledged (useBeaconScanner), so the
 * patrol history re-fetches GET /api/v2/record right after a connect or
 * disconnect lands server-side — the reconcile trigger named by the
 * patrol-record contract — instead of only on tab focus. Not a subscription:
 * usePatrolRecords reads the counter during render (the screen already ticks
 * every second via useNow) and refetches when it changes, so no request is
 * sent per tick, only after an acknowledged event.
 */

let version = 0;

/** Signal that an acknowledged event may have changed the server's records. */
export function notifyRecordsChanged(): void {
  version += 1;
}

/** Return how many record-changing acknowledgements have been signalled. */
export function getRecordsVersion(): number {
  return version;
}

/** Reset the counter. Used by tests. */
export function resetRecordsVersion(): void {
  version = 0;
}
