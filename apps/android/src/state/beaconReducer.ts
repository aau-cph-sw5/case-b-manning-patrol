// decides the next beacon state. pure: no scanning, timers or other side effects.
// events are already ordered by the scanner, so the reducer only folds them in.
import type { BeaconAction, BeaconState } from "@/types/beacon";

// the event log on screen only needs a tail; the backend owns the full append-only record.
const RECENT_EVENT_LIMIT = 20;

export function beaconReducer(state: BeaconState, action: BeaconAction): BeaconState {
  switch (action.type) {
    case "SCAN_STARTED":
      return { ...state, scanning: true };

    case "SCAN_STOPPED":
      // beacons already seen stay connected: losing the scan does not move the steward.
      return { ...state, scanning: false };

    case "EVENT_RECEIVED": {
      const { event } = action;
      const connected = new Set(state.connectedBeaconIds);
      if (event.event === "CONNECTED") {
        connected.add(event.beacon_id);
      } else {
        connected.delete(event.beacon_id);
      }
      return {
        ...state,
        connectedBeaconIds: [...connected],
        recentEvents: [event, ...state.recentEvents].slice(0, RECENT_EVENT_LIMIT),
      };
    }
  }
}
