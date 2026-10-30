import { useEffect, useState } from "react";

import { connectToStationUpdates } from "@/api/stationEventStream";
import type { Station } from "@/types/station";

/** The last station list received over SSE. */
export type StationsSnapshot = {
  stations: Station[];
  /** Phone time in ms since epoch when the list arrived, null before the first event. */
  lastUpdatedAt: number | null;
};

/**
 * Subscribe to the station SSE stream and return the last received snapshot.
 *
 * Connects on mount and disconnects on unmount. The list starts empty and
 * fills with the first event, which the server sends as a full snapshot right
 * on connect; each later event replaces it. Errors are logged and never clear
 * it, so it stays usable offline together with the last update time the
 * screen shows.
 */
export function useStationUpdates(): StationsSnapshot {
  const [snapshot, setSnapshot] = useState<StationsSnapshot>({
    stations: [],
    lastUpdatedAt: null,
  });

  useEffect(() => {
    const disconnect = connectToStationUpdates(
      (data) => {
        // receipt time drives "last updated"; the server clock is not
        // used for it.
        setSnapshot({ stations: data.stations, lastUpdatedAt: Date.now() });
      },
      (error) => {
        console.error("SSE error:", error);
        // nothing to overwrite with; a previously received snapshot is kept on purpose.
      },
    );
    return () => {
      disconnect();
    };
  }, []);

  return snapshot;
}
