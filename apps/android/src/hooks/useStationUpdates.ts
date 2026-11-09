/** Hook exposing the latest station snapshot from the dashboard stream. */
import { useEffect, useState } from "react";

import { connectToStationUpdates } from "@/api/stationEventStream";
import type { Station } from "@/types/station";

/** The last valid dashboard event, as {@link useStationUpdates} keeps it. */
export type StationsSnapshot = {
  /** Empty until the first valid event arrives. */
  stations: Station[];
  /** Device time (epoch ms) the last valid event was received; null before the first. */
  lastUpdatedAt: number | null;
};

/**
 * Subscribe to the dashboard SSE stream and keep the last received snapshot.
 *
 * The list starts empty and fills with the first event, which the server sends
 * as a full snapshot right on connect. A dropped connection or an invalid
 * payload never clears it (errors are only logged), so it stays usable offline
 * together with the last update time the screen shows. Connects once on mount
 * and closes the connection on unmount.
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
