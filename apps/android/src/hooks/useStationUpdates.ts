/** Hook exposing the latest station snapshot and at-risk threshold from the dashboard stream. */
import { useEffect, useState } from "react";

import { connectToStationUpdates } from "@/api/stationEventStream";

import { DEFAULT_AT_RISK_THRESHOLD_MINUTES } from "@/types/config";
import type { Station } from "@/types/station";

/** The last valid dashboard events, as {@link useStationUpdates} keeps them. */
export type StationsSnapshot = {
  /** Empty until the first valid `dashboard` event arrives. */
  stations: Station[];
  /** Device time (epoch ms) the last valid `dashboard` event was received; null before the first. */
  lastUpdatedAt: number | null;
  /**
   * At-risk threshold in minutes, from the latest `at-risk-threshold` event.
   * The backend default until the first one arrives.
   */
  atRiskThresholdMinutes: number;
};

/**
 * Subscribe to the dashboard SSE stream and keep the last received snapshot.
 *
 * The list starts empty and fills with the first `dashboard` event, which the
 * server sends as a full snapshot right on connect. The threshold starts at
 * the backend default and is replaced by each `at-risk-threshold` event, so
 * station colours follow threshold changes made from the control room. A
 * dropped connection or an invalid payload never clears either (errors are
 * only logged), so they stay usable offline together with the last update
 * time the screen shows. Connects once on mount and closes the connection on
 * unmount.
 */
export function useStationUpdates(): StationsSnapshot {
  const [snapshot, setSnapshot] = useState<StationsSnapshot>({
    stations: [],
    lastUpdatedAt: null,
    atRiskThresholdMinutes: DEFAULT_AT_RISK_THRESHOLD_MINUTES,
  });

  useEffect(() => {
    const disconnect = connectToStationUpdates({
      onStations: (data) => {
        // receipt time drives "last updated"; the server clock is not
        // used for it.
        setSnapshot((previous) => ({
          ...previous,
          stations: data.stations,
          lastUpdatedAt: Date.now(),
        }));
      },
      onAtRiskThreshold: (threshold) => {
        setSnapshot((previous) => ({
          ...previous,
          atRiskThresholdMinutes: threshold.atRiskThresholdMinutes,
        }));
      },
      onError: (error) => {
        console.error("SSE error:", error);
        // nothing to overwrite with; previously received state is kept on purpose.
      },
    });
    return () => {
      disconnect();
    };
  }, []);

  return snapshot;
}
