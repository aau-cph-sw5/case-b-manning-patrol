import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

import { postConnectionEvent } from "@/api/postConnectionEvent";
import { BeaconEventService } from "@/services/BeaconEventService";
import { scanReducer } from "@/state/scanReducer";
import { showToast } from "@/state/toast";
import { initialScanState, type BeaconConnectionEvent } from "@/types/beacon";
import type { BeaconScanner } from "@/types/BeaconScanner";

/** What {@link useBeaconScanner} returns. */
export type UseBeaconScannerResult = {
  /** Raw scanner events as seen on screen, before any debouncing. */
  state: ReturnType<typeof scanReducer>;
  /** Start the scanner and mark the scan as running. */
  start: () => void;
  /** Stop the scanner and drop any pending connect/disconnect confirmations. */
  stop: () => void;
};

/**
 * Run a beacon scan for a screen and forward confirmed connections.
 *
 * Every raw scanner event updates `state`. Events also pass through a
 * {@link BeaconEventService}; only the connects and disconnects it confirms
 * show a toast and are POSTed to the backend. A failed POST is logged as a
 * warning and not retried.
 *
 * On unmount the scanner is stopped and pending confirmations are dropped
 * without being sent. That is safe when a session stop follows: the backend
 * closes a device's open connections on `patrol-session/stop`.
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
