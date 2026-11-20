/**
 * Stands in for the real BLE scanner: simulates a steward walking past beacons,
 * connecting to one, holding it for a while, losing it, then reaching the next.
 *
 * No Bluetooth is involved, so it runs in Expo Go and on the emulator; the real
 * scanner can be dropped in behind the same {@link BeaconScanner} interface.
 */
import type { BeaconConnectionEvent, BeaconEventKind } from "@/types/beacon";
import {
  MOCK_BEACON_IDS,
  MOCK_CONCOURSE_BEACON_IDS,
} from "@/fixtures/mockBeacons";
import type { BeaconScanner } from "@/types/BeaconScanner";

/** One event in the deterministic end-to-end fixture replay. */
export type FixtureReplayEvent = {
  event: BeaconEventKind;
  beacon_id: string;
  offsetMs: number;
};

/**
 * The first pass resets every dashboard timer together. Later passes simulate
 * a steward moving through one station at a time.
 *
 * All station pairs are connected together at demo start and disconnected
 * together after four simulated minutes. With the default speed of 10, the
 * complete dashboard replay takes about 24 seconds.
 */
const ALL_STATION_BEACONS = MOCK_BEACON_IDS.map(
  (platformBeacon, index) => ({
    platformBeacon,
    concourseBeacon: MOCK_CONCOURSE_BEACON_IDS[index]!,
  }),
);

export const INITIAL_RESET_EVENTS: readonly FixtureReplayEvent[] =
  ALL_STATION_BEACONS.flatMap(({ platformBeacon, concourseBeacon }) => [
    { event: "CONNECTED", beacon_id: platformBeacon, offsetMs: 0 },
    { event: "CONNECTED", beacon_id: concourseBeacon, offsetMs: 0 },
    { event: "DISCONNECTED", beacon_id: platformBeacon, offsetMs: 240_000 },
    { event: "DISCONNECTED", beacon_id: concourseBeacon, offsetMs: 240_000 },
  ]);

// At the documented 10x demo speed this is 24 real seconds, exceeding the
// concourse qualification threshold of 20 seconds.
const PATROL_VISIT_DURATION_MS = 240_000;
const PATROL_TRAVEL_INTERVAL_MS = 300_000;

export const PATROL_REPLAY_EVENTS: readonly FixtureReplayEvent[] =
  ALL_STATION_BEACONS.flatMap(({ platformBeacon, concourseBeacon }, index) => {
    const arrival = index * PATROL_TRAVEL_INTERVAL_MS;
    const departure = arrival + PATROL_VISIT_DURATION_MS;
    return [
      { event: "CONNECTED", beacon_id: platformBeacon, offsetMs: arrival },
      { event: "CONNECTED", beacon_id: concourseBeacon, offsetMs: arrival },
      { event: "DISCONNECTED", beacon_id: platformBeacon, offsetMs: departure },
      { event: "DISCONNECTED", beacon_id: concourseBeacon, offsetMs: departure },
    ];
  });

/** Backwards-compatible name for the initial full-station reset timeline. */
export const FIXTURE_REPLAY_EVENTS = INITIAL_RESET_EVENTS;

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

/**
 * Create a deterministic scanner that replays the end-to-end fixture timeline.
 *
 * Events are rebased to the time scanning starts and emitted as confirmed
 * events. The initial reset runs once. If `patrolEvents` are provided, they
 * repeat after the reset and represent the ongoing patrol route.
 */
export function createFixtureBeaconScanner(
  events: readonly FixtureReplayEvent[] = INITIAL_RESET_EVENTS,
  speed = 60,
  patrolEvents: readonly FixtureReplayEvent[] = [],
): BeaconScanner {
  if (!Number.isFinite(speed) || speed <= 0) {
    throw new Error("Fixture replay speed must be greater than zero");
  }

  let timers: ReturnType<typeof setTimeout>[] = [];
  let currentListener: ((event: BeaconConnectionEvent) => void) | null = null;
  let replayGeneration = 0;
  function stop() {
    replayGeneration += 1;
    for (const timer of timers) {
      clearTimeout(timer);
    }
    timers = [];
    currentListener = null;
  }

  function start(listener: (event: BeaconConnectionEvent) => void) {
    stop();
    currentListener = listener;
    const generation = replayGeneration;

    function scheduleBatch(
      batch: readonly FixtureReplayEvent[],
      onComplete: () => void,
    ) {
      if (currentListener === null || generation !== replayGeneration) {
        return;
      }

      const startedAt = Date.now();
      timers = batch.map((fixtureEvent) =>
        setTimeout(() => {
          currentListener?.({
            event: fixtureEvent.event,
            beacon_id: fixtureEvent.beacon_id,
            timestamp: new Date(
              startedAt + fixtureEvent.offsetMs / speed,
            ).toISOString(),
          });
        }, fixtureEvent.offsetMs / speed),
      );
      if (batch.length > 0) {
        timers.push(
          setTimeout(
            onComplete,
            Math.max(...batch.map((event) => event.offsetMs)) / speed + 1,
          ),
        );
      } else {
        onComplete();
      }
    }

    function schedulePatrolRound() {
      if (currentListener === null || generation !== replayGeneration) {
        return;
      }
      scheduleBatch(patrolEvents, schedulePatrolRound);
    }

    scheduleBatch(
      events,
      patrolEvents.length > 0
        ? () => {
            timers = [];
            schedulePatrolRound();
          }
        : () => {
            timers = [];
          },
    );
  }

  return {
    start,
    stop,
    eventsAreConfirmed: true,
  };
}
