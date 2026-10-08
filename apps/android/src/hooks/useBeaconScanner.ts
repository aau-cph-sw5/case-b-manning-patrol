import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

import { postConnectionEvent } from "@/api/postConnectionEvent";
import { BeaconEventService } from "@/services/BeaconEventService";
import { scanReducer } from "@/state/scanReducer";
import { initialScanState, type BeaconConnectionEvent } from "@/types/beacon";
import type { BeaconScanner } from "@/types/BeaconScanner";

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
  const eventService = useMemo(
    () =>
      new BeaconEventService((event) => {
        postConnectionEvent(event).catch((error: unknown) => {
          console.warn(`could not forward ${event.event} for ${event.beacon_id}:`, error);
        });
      }),
    [],
  );

  useEffect(() => {
    scannerRef.current = scanner;
  }, [scanner]);

  const onEvent = useCallback((event: BeaconConnectionEvent) => {
    dispatch({ type: "EVENT_RECEIVED", event });
    eventService.handleEvent(event);
  }, [eventService]);

  // stop scanning when the screen goes away, so no events reach a dead listener
  useEffect(() => {
    return () => {
      scannerRef.current.stop();
      eventService.reset();
    };
  }, [eventService]);

  const start = useCallback(() => {
    scannerRef.current.start(onEvent);
    dispatch({ type: "SCAN_STARTED" });
  }, [onEvent]);

  const stop = useCallback(() => {
    scannerRef.current.stop();
    eventService.reset();
    dispatch({ type: "SCAN_STOPPED" });
  }, [eventService]);

  return { state, start, stop };
}
