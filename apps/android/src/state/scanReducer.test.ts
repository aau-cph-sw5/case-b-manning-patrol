// the reducer is pure: every case is just (state, action) in, next state out.
import { describe, expect, it } from "vitest";

import { scanReducer } from "@/state/scanReducer";
import { initialScanState, type BeaconEvent } from "@/types/beacon";

const event = (partial: Partial<BeaconEvent>): BeaconEvent => ({
  event: "CONNECTED",
  beacon_id: "beacon-1",
  android_id: "steward-1",
  timestamp: "2026-05-30T03:08:13.000Z",
  ...partial,
});

describe("scanReducer", () => {
  it("connects and disconnects beacon ids", () => {
    let state = scanReducer(initialScanState, {
      type: "EVENT_RECEIVED",
      event: event({ beacon_id: "beacon-1" }),
    });
    state = scanReducer(state, {
      type: "EVENT_RECEIVED",
      event: event({ beacon_id: "beacon-2" }),
    });
    expect(state.connectedBeaconIds).toEqual(["beacon-1", "beacon-2"]);

    state = scanReducer(state, {
      type: "EVENT_RECEIVED",
      event: event({ event: "DISCONNECTED", beacon_id: "beacon-1" }),
    });
    expect(state.connectedBeaconIds).toEqual(["beacon-2"]);
  });

  it("keeps the 20 most recent events, newest first", () => {
    let state = initialScanState;
    for (let i = 0; i < 25; i++) {
      state = scanReducer(state, {
        type: "EVENT_RECEIVED",
        event: event({ beacon_id: `beacon-${i}` }),
      });
    }
    expect(state.recentEvents).toHaveLength(20);
    expect(state.recentEvents[0]!.beacon_id).toBe("beacon-24");
    expect(state.recentEvents[19]!.beacon_id).toBe("beacon-5");
  });

  it("toggles scanning without dropping connected beacons on stop", () => {
    let state = scanReducer(initialScanState, { type: "SCAN_STARTED" });
    state = scanReducer(state, {
      type: "EVENT_RECEIVED",
      event: event({ beacon_id: "beacon-1" }),
    });
    expect(state.scanning).toBe(true);

    state = scanReducer(state, { type: "SCAN_STOPPED" });
    expect(state.scanning).toBe(false);
    expect(state.connectedBeaconIds).toEqual(["beacon-1"]);
  });
});
