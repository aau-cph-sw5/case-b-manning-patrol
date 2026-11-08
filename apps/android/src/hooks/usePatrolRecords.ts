// the patrol history for a screen: the steward's records for the current
// shift, fetched from the backend on mount and re-fetched through refetch()
// when the screen regains focus (the reconcile step of the patrol-record
// contract, contracts/api/v2/patrol-record). a failed fetch keeps the last
// good list, so a dropped connection never blanks the history. a successful
// fetch also re-sends pending connection events (services/pendingEventSync)
// and fetches once more, so pendings (state/pendingRecords) whose events the
// backend never received are retired instead of staying pending forever; the
// screen merges the rest back in at render time. refetch also fires whenever
// an ingestion POST is acknowledged (state/recordRefresh), so the history
// reconciles right after each connect/disconnect without polling.
import { useCallback, useEffect, useRef, useState } from "react";

import { getPatrolRecords } from "@/api/getPatrolRecords";
import { MOCK_ANDROID_ID } from "@/fixtures/mockBeacons";
import { retryPendingConnectionEvents } from "@/services/pendingEventSync";
import { removeReconciledPendingRecords } from "@/state/pendingRecords";
import { getRecordsVersion } from "@/state/recordRefresh";
import type { Record, RecordList } from "@/types/patrol_records/record";

// For a real-device build, restore DeviceInfo.getAndroidId(); Expo Go uses the mock ID.
const STEWARD_ID = MOCK_ANDROID_ID;

// shown to the steward. the api's own error message is meant for developers.
const FETCH_ERROR = "Kunne ikke hente historikken. Prøv igen.";

/**
 * Re-send pending connection events after a successful fetch, then fetch once
 * more so the stored records retire their pendings.
 *
 * A successful fetch means the backend is reachable again. The retry runs
 * before the follow-up fetch's reconcile, otherwise a still-open server record
 * would drop a pending closed whose disconnect was never delivered.
 */
async function flushPendingsAfterFetch(
  isCancelled: () => boolean,
  applyList: (list: RecordList) => void,
): Promise<void> {
  const sent = await retryPendingConnectionEvents();
  if (sent === 0 || isCancelled()) return;
  try {
    const fresh = await getPatrolRecords(STEWARD_ID);
    if (isCancelled()) return;
    applyList(fresh);
  } catch {
    // keep the list we already have; the pendings retry on the next success
  }
}

export type UsePatrolRecordsResult = {
  records: Record[];
  // server time the current list was built at; null until the first response.
  serverTime: Date | null;
  loading: boolean;
  error: string | null;
  // fetches the records again. does nothing while a request is in flight.
  refetch: () => Promise<void>;
};

export function usePatrolRecords(): UsePatrolRecordsResult {
  const [records, setRecords] = useState<Record[]>([]);
  const [serverTime, setServerTime] = useState<Date | null>(null);
  // true from the start: the mount effect below fetches immediately
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // a focus refetch can land while the mount fetch is still running; this stops a second request
  const requestInFlight = useRef(false);

  // the fetch is the reconcile step: server records retire matching pendings
  const applyList = useCallback((list: RecordList) => {
    removeReconciledPendingRecords(list.records);
    setRecords(list.records);
    setServerTime(list.time);
  }, []);

  // re-send the events the backend never acknowledged, then fetch once more so
  // those stored records retire their pendings (see flushPendingsAfterFetch)
  const flushPendings = useCallback(
    (isCancelled: () => boolean) => flushPendingsAfterFetch(isCancelled, applyList),
    [applyList],
  );

  // the mount fetch reports through the promise callbacks, so the effect
  // body itself never calls setState
  useEffect(() => {
    let cancelled = false;
    requestInFlight.current = true;
    void getPatrolRecords(STEWARD_ID).then(
      (list) => {
        requestInFlight.current = false;
        if (cancelled) return;
        applyList(list);
        setError(null);
        setLoading(false);
        void flushPendings(() => cancelled);
      },
      () => {
        requestInFlight.current = false;
        if (cancelled) return;
        setError(FETCH_ERROR);
        setLoading(false);
      },
    );
    return () => {
      cancelled = true;
    };
  }, [applyList, flushPendings]);

  const refetch = useCallback(async () => {
    if (requestInFlight.current) return;
    requestInFlight.current = true;
    setLoading(true);
    setError(null);
    try {
      const list = await getPatrolRecords(STEWARD_ID);
      applyList(list);
      void flushPendings(() => false);
    } catch {
      setError(FETCH_ERROR);
    } finally {
      requestInFlight.current = false;
      setLoading(false);
    }
  }, [applyList, flushPendings]);

  // event-driven reconcile (patrol-record contract: re-fetch when an ingestion
  // request is acknowledged): useBeaconScanner bumps the version on every
  // acked connect/disconnect POST. The effect runs on every render — the
  // screen ticks each second via useNow — but only fires a request when the
  // version actually changed, so there is no per-second polling.
  const lastSeenVersion = useRef(getRecordsVersion());
  useEffect(() => {
    const version = getRecordsVersion();
    if (version !== lastSeenVersion.current) {
      lastSeenVersion.current = version;
      void refetch();
    }
  });

  return { records, serverTime, loading, error, refetch };
}
