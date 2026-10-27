// the station list for a screen: subscribes to the SSE datastream and keeps the
// last received snapshot. the list starts empty and fills with the first
// event, which the server sends as a full snapshot right on connect. a
// dropped connection never clears it, so it stays usable offline together
// with the last update time the screen shows.
import { useEffect, useState } from "react";

import { connectToStationUpdates } from "@/api/stationEventStream";
import type { Station } from "@/types/station";

export type StationsSnapshot = {
  stations: Station[];
  lastUpdatedAt: number | null;
};

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
