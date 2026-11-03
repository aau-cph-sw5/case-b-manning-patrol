// the patrol history for a screen: the steward's records for the current
// shift, fetched from the backend on mount and re-fetched through refetch()
// when the screen regains focus (the reconcile step of the patrol-record
// contract, contracts/api/v2/patrol-record). a failed fetch keeps the last
// good list, so a dropped connection never blanks the history.
import { useCallback, useEffect, useRef, useState } from "react";

import { getPatrolRecords } from "@/api/getPatrolRecords";
import { MOCK_ANDROID_ID } from "@/fixtures/mockBeacons";
import type { Record } from "@/types/patrol_records/record";

// For a real-device build, restore DeviceInfo.getAndroidId(); Expo Go uses the mock ID.
const STEWARD_ID = MOCK_ANDROID_ID;

// shown to the steward. the api's own error message is meant for developers.
const FETCH_ERROR = "Kunne ikke hente historikken. Prøv igen.";

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

  // the mount fetch reports through the promise callbacks, so the effect
  // body itself never calls setState
  useEffect(() => {
    let cancelled = false;
    requestInFlight.current = true;
    void getPatrolRecords(STEWARD_ID).then(
      (list) => {
        requestInFlight.current = false;
        if (cancelled) return;
        setRecords(list.records);
        setServerTime(list.time);
        setError(null);
        setLoading(false);
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
  }, []);

  const refetch = useCallback(async () => {
    if (requestInFlight.current) return;
    requestInFlight.current = true;
    setLoading(true);
    setError(null);
    try {
      const list = await getPatrolRecords(STEWARD_ID);
      setRecords(list.records);
      setServerTime(list.time);
    } catch {
      setError(FETCH_ERROR);
    } finally {
      requestInFlight.current = false;
      setLoading(false);
    }
  }, []);

  return { records, serverTime, loading, error, refetch };
}
