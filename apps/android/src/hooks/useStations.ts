// the station list for a screen: fetches the broadcast array and keeps the last
// successful snapshot. a dropped connection never clears the list, so it stays
// usable offline together with the last update time the screen shows.
import { useEffect, useState } from "react";

import { fetchStations, type StationsSnapshot } from "@/api/stations";
import type { StationRecord } from "@/types/station";

export type UseStationsResult = {
  stations: StationRecord[];
  lastUpdatedAt: number | null;
};

export function useStations(): UseStationsResult {
  const [snapshot, setSnapshot] = useState<StationsSnapshot | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchStations()
      .then((next) => {
        if (!cancelled) setSnapshot(next);
      })
      .catch(() => {
        // nothing to show yet; a previously loaded snapshot is kept on purpose.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return {
    stations: snapshot?.stations ?? [],
    lastUpdatedAt: snapshot?.lastUpdatedAt ?? null,
  };
}
