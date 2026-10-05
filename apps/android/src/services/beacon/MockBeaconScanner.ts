// stands in for the real BLE scanner: simulates a steward walking past beacons, connecting
// to one, holding it for a while, losing it, then reaching the next. no Bluetooth is
// involved, so it runs in Expo Go and on the emulator; the real scanner can be dropped in
// behind the same BeaconScanner interface.
import type { BeaconEvent, BeaconEventKind } from "@/types/beacon";
import { MOCK_BEACON_IDS } from "@/services/beacon/mockBeacons";
import type { BeaconScanner } from "@/services/beacon/scanner";

export type MockBeaconScannerOptions = {
  // the device this phone claims to be.
  android_id: string;
  beacon_ids?: readonly string[];
  // how often the simulation steps forward, and how many steps a connection lasts.
  tick_ms?: number;
  hold_ticks?: number;
};

const DEFAULT_TICK_MS = 3000;
const DEFAULT_HOLD_TICKS = 2;

export function createMockBeaconScanner(options: MockBeaconScannerOptions): BeaconScanner {
  const {
    android_id,
    beacon_ids = MOCK_BEACON_IDS,
    tick_ms = DEFAULT_TICK_MS,
    hold_ticks = DEFAULT_HOLD_TICKS,
  } = options;

  let timer: ReturnType<typeof setInterval> | null = null;
  let listener: ((event: BeaconEvent) => void) | null = null;
  let nextBeaconIndex = 0;
  let ticksHeld = 0;
  let connectedBeaconId: string | null = null;

  function emit(event: BeaconEventKind, beacon_id: string) {
    listener?.({ event, beacon_id, android_id, timestamp: new Date().toISOString() });
  }

  function step() {
    if (connectedBeaconId === null) {
      // the steward reaches the next beacon on the route
      connectedBeaconId = beacon_ids[nextBeaconIndex % beacon_ids.length]!;
      nextBeaconIndex += 1;
      ticksHeld = 0;
      emit("CONNECTED", connectedBeaconId);
      return;
    }
    ticksHeld += 1;
    if (ticksHeld >= hold_ticks) {
      // the steward walks out of range
      emit("DISCONNECTED", connectedBeaconId);
      connectedBeaconId = null;
    }
  }

  return {
    start(nextListener) {
      stopTimer();
      listener = nextListener;
      timer = setInterval(step, tick_ms);
    },
    stop() {
      stopTimer();
      listener = null;
    },
  };

  function stopTimer() {
    if (timer !== null) {
      clearInterval(timer);
      timer = null;
    }
  }
}
