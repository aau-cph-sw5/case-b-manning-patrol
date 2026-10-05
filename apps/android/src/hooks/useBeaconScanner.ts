// connects the scanner to the state: start/stop the scan and fold every event into the
// reducer. the scanner is passed in, so this hook contains no Bluetooth code and works
// unchanged with the real BLE scanner later.
import { useCallback, useEffect, useReducer, useRef } from "react";

import { beaconReducer } from "@/state/beaconReducer";
import { initialBeaconState, type BeaconEvent } from "@/types/beacon";
import type { BeaconScanner } from "@/services/beacon/scanner";

export type UseBeaconScannerResult = {
  state: ReturnType<typeof beaconReducer>;
  // starts a stopped scan or stops a running one.
  start: () => void;
  stop: () => void;
};

export function useBeaconScanner(scanner: BeaconScanner): UseBeaconScannerResult {
  const [state, dispatch] = useReducer(beaconReducer, initialBeaconState);

  // the scanner changes identity between renders; keep the latest one for cleanup
  const scannerRef = useRef(scanner);
  scannerRef.current = scanner;

  const onEvent = useCallback((event: BeaconEvent) => {
    dispatch({ type: "EVENT_RECEIVED", event });
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
