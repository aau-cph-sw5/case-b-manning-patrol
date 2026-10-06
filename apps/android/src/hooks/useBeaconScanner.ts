// TODO(MET-B-004, "edge cases - business logic", owned by <mate>): the scanner reports
// raw connect/disconnect events and they are forwarded to the backend as they arrive,
// and the scan runs only while the session is active (done in app/index.tsx). the record
// rules of MET-B-004 are not implemented yet:
//  - session gating at the record level: even if events leak in from outside a session,
//    a connection outside an active session creates nothing (AC 1).
//  - x-second hold: within a session a record initiates once a beacon has been connected
//    for x seconds; a connection that never reaches x seconds is discarded (AC 2).
//  - tolerated gap: a disconnect that returns within the tolerated gap continues the same
//    record instead of opening a second one (ADR 0006 tolerated-gap-decision).
//  - close on loss: a record closes when the connection has been lost for longer than the
//    tolerated gap; its end time is the last confirmed connection (AC 4).
//  - close on stop: pressing stop closes every open record at its last confirmed
//    connection; connections shorter than x seconds were never records and are discarded
//    (AC 5).
//  - concurrent records: records for more than one area may be open at the same time
//    (AC 6); the mock must eventually emit overlapping connections to exercise this.
//  - area attribution: every record carries which area it was taken in (AC 7).
// connects the scanner to the state: start/stop the scan, fold every event into the
// reducer and forward it to the backend. the scanner is passed in, so this hook contains
// no Bluetooth code and works unchanged with the real BLE scanner later.
import { useCallback, useEffect, useReducer, useRef } from "react";

import { postConnectionEvent } from "@/api/postConnectionEvent";
import { scanReducer } from "@/state/scanReducer";
import { initialScanState, type BeaconConnectionEvent } from "@/types/beacon";
import type { BeaconScanner } from "@/services/beacon/scanner";

export type UseBeaconScannerResult = {
  state: ReturnType<typeof scanReducer>;
  // starts a stopped scan or stops a running one.
  start: () => void;
  stop: () => void;
};

export function useBeaconScanner(scanner: BeaconScanner): UseBeaconScannerResult {
  const [state, dispatch] = useReducer(scanReducer, initialScanState);

  // the scanner changes identity between renders; keep the latest one for cleanup and
  // for start/stop, without re-creating the callbacks every render
  const scannerRef = useRef(scanner);

  useEffect(() => {
    scannerRef.current = scanner;
  }, [scanner]);

  const onEvent = useCallback((event: BeaconConnectionEvent) => {
    dispatch({ type: "EVENT_RECEIVED", event });
    // fire and forget: a rejected send must not stop the scan, but it should be visible
    // in the terminal while the backend connection is still flaky in development
    postConnectionEvent(event).catch((error: unknown) => {
      console.warn(`could not forward ${event.event} for ${event.beacon_id}:`, error);
    });
  }, []);

  // stop scanning when the screen goes away, so no events reach a dead listener
  useEffect(() => {
    return () => scannerRef.current.stop();
  }, []);

  const start = useCallback(() => {
    scannerRef.current.start(onEvent);
    dispatch({ type: "SCAN_STARTED" });
  }, [onEvent]);

  const stop = useCallback(() => {
    scannerRef.current.stop();
    dispatch({ type: "SCAN_STOPPED" });
  }, []);

  return { state, start, stop };
}
