/**
 * Re-send connection events the backend never acknowledged.
 *
 * A failed connect/disconnect POST leaves its pending placeholder in
 * state/pendingRecords, and the server's record list can only reconcile that
 * pending once the event actually reaches the backend. So after any
 * successful GET (the signal that connectivity is back) the app re-POSTs
 * every pending event with its original device timestamp — the phone is the
 * source of origin (ADR-0004) — and the caller fetches once more so the
 * stored records retire the pendings.
 */
import { postConnectionEvent } from "@/api/postConnectionEvent";
import { getPendingRecords } from "@/state/pendingRecords";
import type { BeaconConnectionEvent } from "@/types/beacon";

/**
 * POST every pending connection again, oldest first.
 *
 * A closed pending is re-sent as its CONNECTED followed by its DISCONNECTED:
 * the backend pairs a disconnect with the latest stored connect for the
 * beacon, so a disconnect without its connect would create no record and the
 * pending could never reconcile. Both carry their original device timestamps.
 *
 * @returns How many events the backend accepted. Events that still fail keep
 *   their pending and are retried on the next successful fetch.
 */
export async function retryPendingConnectionEvents(): Promise<number> {
  let sent = 0;
  for (const pending of getPendingRecords()) {
    const events: BeaconConnectionEvent[] = [
      { event: "CONNECTED", beacon_id: pending.beaconId, timestamp: pending.startedAt.toISOString() },
    ];
    if (pending.status === "closed") {
      events.push({
        event: "DISCONNECTED",
        beacon_id: pending.beaconId,
        timestamp: (pending.endedAt ?? pending.startedAt).toISOString(),
      });
    }
    for (const event of events) {
      try {
        await postConnectionEvent(event);
        sent += 1;
      } catch {
        // still unreachable; the pending stays and the next successful fetch retries again
        break;
      }
    }
  }
  return sent;
}
