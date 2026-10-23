// the station list for a screen: subscribes to the SSE datastream and keeps the
// last received snapshot. a dropped connection never clears the list, so it
// stays usable offline together with the last update time the screen shows.
// the snapshot starts from the mock fixture until the real stream is live.
import { useEffect, useState } from "react";

import { connectToStationUpdates } from "@/api/stationEventStream";
import { createMockStations } from "@/fixtures/mockStations";
import type { Station } from "@/types/station";

export type StationsSnapshot = {
  stations: Station[];
  lastUpdatedAt: number | null;
};

export function useStationUpdates(): StationsSnapshot {
  // seeded with the mock broadcast until SSE_URL is live; delete the
  // initializer's body for an empty start instead.
  const [snapshot, setSnapshot] = useState<StationsSnapshot>(() => ({
    stations: createMockStations(Date.now()),
    lastUpdatedAt: null,
  }));

  useEffect(() => {
    const disconnect = connectToStationUpdates(
      (data) => {
        // the payload carries no backend timestamp, so the client receipt
        // time is the best "last updated" we have.
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
