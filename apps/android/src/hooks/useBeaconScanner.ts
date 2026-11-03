/** React binding for a beacon scanner that forwards confirmed events to the backend. */
import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

import { postConnectionEvent } from "@/api/postConnectionEvent";
import { BeaconEventService } from "@/services/BeaconEventService";
import { scanReducer } from "@/state/scanReducer";
import { showToast } from "@/state/toast";
import { initialScanState, type BeaconConnectionEvent } from "@/types/beacon";
import type { BeaconScanner } from "@/types/BeaconScanner";

/** What {@link useBeaconScanner} returns. */
export type UseBeaconScannerResult = {
  /** Built from the raw scanner events, before any confirmation delay. */
  state: ReturnType<typeof scanReducer>;
  /** Start scanning. Calling it while scanning restarts the scanner with a fresh listener. */
  start: () => void;
  /** Stop scanning and drop every connect or disconnect still waiting for confirmation. */
  stop: () => void;
};

/**
 * Drive a beacon scanner and forward its confirmed events to the backend.
 *
 * Raw scanner events update `state` at once. They also pass through a
 * {@link BeaconEventService}, which confirms a connection after 3 s and a
 * disconnection after 10 s without reconnecting. Each confirmed event shows a
 * toast and is posted with {@link postConnectionEvent}; a failed post is
 * logged with `console.warn` and not retried.
 *
 * `start` and `stop` keep their identity across renders and always use the
 * latest `scanner`. On unmount the scanner is stopped and pending
 * confirmations are dropped.
 */
export function useBeaconScanner(scanner: BeaconScanner): UseBeaconScannerResult {
  const [state, dispatch] = useReducer(scanReducer, initialScanState);

  // the scanner changes identity between renders; keep the latest one for cleanup and
  // for start/stop, without re-creating the callbacks every render
  const scannerRef = useRef(scanner);
  const eventService = useMemo(
    () =>
      new BeaconEventService((event) => {
        // fires once per confirmed connection: the beacon survived qualification (connect)
        // or the disconnect confirmation delay, i.e. the same moment the POST leaves the phone.
        const message =
          event.event === "CONNECTED"
            ? `Forbundet til beacon`
            : `Afbrudt fra beacon`;
        showToast(message);

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
