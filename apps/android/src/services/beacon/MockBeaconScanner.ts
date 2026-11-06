/**
 * Stands in for the real BLE scanner: simulates a steward walking past beacons,
 * connecting to one, holding it for a while, losing it, then reaching the next.
 *
 * No Bluetooth is involved, so it runs in Expo Go and on the emulator; the real
 * scanner can be dropped in behind the same {@link BeaconScanner} interface.
 */
import type { BeaconConnectionEvent, BeaconEventKind } from "@/types/beacon";
import { MOCK_BEACON_IDS } from "@/fixtures/mockBeacons";
import type { BeaconScanner } from "@/types/BeaconScanner";

/** Settings for {@link createMockBeaconScanner}. */
export type MockBeaconScannerOptions = {
  /** The device this phone claims to be. Not read by the scanner: its events carry no device id. */
  android_id: string;
  /** Beacons to visit in order; defaults to all {@link MOCK_BEACON_IDS}. */
  beacon_ids?: readonly string[];
  /** [min, max) in ms of how long a beacon stays connected. */
  connectionDurationRangeMs?: readonly [number, number];
  /** [min, max) in ms of how long until the next beacon arrives. */
  nextBeaconArrivalDelayRangeMs?: readonly [number, number];
};

const DEFAULT_CONNECTION_DURATION_RANGE_MS: readonly [number, number] = [9_000, 45_000];
const DEFAULT_NEXT_BEACON_ARRIVAL_DELAY_RANGE_MS: readonly [number, number] = [
  2_000,
  12_000,
];

/** Return a uniformly random delay in [min, max). */
function randomDelay(range: readonly [number, number]): number {
  return range[0] + Math.random() * (range[1] - range[0]);
}

/**
 * Create a scanner that simulates a steward walking past beacons.
 *
 * `start` connects to the next beacon at once and keeps scheduling further
 * arrivals after random delays; each connection ends with a DISCONNECTED after
 * a random duration, so several beacons can be connected at the same time.
 * Beacons are visited round robin and revisited only after their previous
 * connection has ended. `stop` cancels every timer without emitting
 * DISCONNECTED for beacons still connected. Starting again resumes with the
 * next beacon in the list.
 */
export function createMockBeaconScanner(options: MockBeaconScannerOptions): BeaconScanner {
  const {
    beacon_ids = MOCK_BEACON_IDS,
    connectionDurationRangeMs = DEFAULT_CONNECTION_DURATION_RANGE_MS,
    nextBeaconArrivalDelayRangeMs = DEFAULT_NEXT_BEACON_ARRIVAL_DELAY_RANGE_MS,
  } = options;

  const activeConnections = new Map<string, ReturnType<typeof setTimeout>>();
  let nextConnectionTimer: ReturnType<typeof setTimeout> | null = null;
  let currentListener: ((event: BeaconConnectionEvent) => void) | null = null;
  let nextBeaconIndex = 0;

  function emit(event: BeaconEventKind, beacon_id: string) {
    if (currentListener !== null) {
      currentListener({ event, beacon_id, timestamp: new Date().toISOString() });
    }
  }

  function scheduleNextConnection() {
    if (currentListener === null || nextConnectionTimer !== null) {
      return;
    }

    nextConnectionTimer = setTimeout(() => {
      nextConnectionTimer = null;
      connectNext();
    }, randomDelay(nextBeaconArrivalDelayRangeMs));
  }

  function connectNext() {
    if (currentListener === null || beacon_ids.length === 0) {
      return;
    }

    // Revisit only after a beacon's previous connection has ended.
    let beaconId: string | undefined;
    for (let attempt = 0; attempt < beacon_ids.length; attempt += 1) {
      const candidate = beacon_ids[nextBeaconIndex % beacon_ids.length]!;
      nextBeaconIndex += 1;
      if (!activeConnections.has(candidate)) {
        beaconId = candidate;
        break;
      }
    }
    if (beaconId === undefined) {
      return;
    }

    emit("CONNECTED", beaconId);
    const disconnectTimer = setTimeout(() => {
      activeConnections.delete(beaconId);
      emit("DISCONNECTED", beaconId);
      scheduleNextConnection();
    }, randomDelay(connectionDurationRangeMs));
    activeConnections.set(beaconId, disconnectTimer);

    // Other configured beacons can connect before this one disconnects.
    scheduleNextConnection();
  }

  function startFunction(nextListener: (event: BeaconConnectionEvent) => void) {
    stopTimer();
    currentListener = nextListener;
    connectNext();
  }

  function stopFunction() {
    stopTimer();
    currentListener = null;
  }

  const scanner: BeaconScanner = {
    start: startFunction,
    stop: stopFunction,
  };
  return scanner;

  function stopTimer() {
    if (nextConnectionTimer !== null) {
      clearTimeout(nextConnectionTimer);
      nextConnectionTimer = null;
    }
    for (const timer of activeConnections.values()) {
      clearTimeout(timer);
    }
    activeConnections.clear();
  }
}
