// stands in for the real BLE scanner: simulates a steward walking past beacons, connecting
// to one, holding it for a while, losing it, then reaching the next. no Bluetooth is
// involved, so it runs in Expo Go and on the emulator; the real scanner can be dropped in
// behind the same BeaconScanner interface.
import type { BeaconConnectionEvent, BeaconEventKind } from "@/types/beacon";
import { MOCK_BEACON_IDS } from "@/fixtures/mockBeacons";
import type { BeaconScanner } from "@/services/beacon/scanner";

export type MockBeaconScannerOptions = {
  // the device this phone claims to be.
  android_id: string;
  beacon_ids?: readonly string[];
  // how long each connection is held and how long the walk to the next beacon takes.
  // both are randomized per cycle, so a new beacon is picked up roughly every 5-15
  // seconds instead of the demo ticking like a clock.
  holdRangeMs?: readonly [number, number];
  walkRangeMs?: readonly [number, number];
};

const DEFAULT_HOLD_RANGE_MS: readonly [number, number] = [3_000, 9_000];
const DEFAULT_WALK_RANGE_MS: readonly [number, number] = [2_000, 6_000];

function randomDelay(range: readonly [number, number]): number {
  return range[0] + Math.random() * (range[1] - range[0]);
}

export function createMockBeaconScanner(options: MockBeaconScannerOptions): BeaconScanner {
  const {
    android_id,
    beacon_ids = MOCK_BEACON_IDS,
    holdRangeMs = DEFAULT_HOLD_RANGE_MS,
    walkRangeMs = DEFAULT_WALK_RANGE_MS,
  } = options;

  let timer: ReturnType<typeof setTimeout> | null = null;
  let listener: ((event: BeaconConnectionEvent) => void) | null = null;
  let nextBeaconIndex = 0;

  function emit(event: BeaconEventKind, beacon_id: string) {
    listener?.({ event, beacon_id, android_id, timestamp: new Date().toISOString() });
  }

  function connectNext() {
    // the steward reaches the next beacon on the route
    const beaconId = beacon_ids[nextBeaconIndex % beacon_ids.length]!;
    nextBeaconIndex += 1;
    emit("CONNECTED", beaconId);
    // the connection holds for a while before the steward walks out of range
    timer = setTimeout(() => {
      emit("DISCONNECTED", beaconId);
      timer = setTimeout(connectNext, randomDelay(walkRangeMs));
    }, randomDelay(holdRangeMs));
  }

  return {
    start(nextListener) {
      stopTimer();
      listener = nextListener;
      // the steward is already next to a beacon when the scan begins: connect at once,
      // instead of making the demo wait for something to happen
      connectNext();
    },
    stop() {
      stopTimer();
      listener = null;
    },
  };

  function stopTimer() {
    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }
  }
}
