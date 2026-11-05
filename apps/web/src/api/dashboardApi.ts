/**
 * Types and clients for the dashboard and trains Server-Sent Events streams,
 * `GET /api/v2/dashboard/stream` and `GET /api/v2/trains/stream`
 * (position-interface/v2 contract).
 *
 * The backend URL comes from `VITE_API_URL` and defaults to
 * http://localhost:8000.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/** API version prefix for all stream endpoints (position-interface/v2 contract). */
const API_VERSION = "/api/v2";

/** Kind of patrol area, as defined in the position-interface/v2 contract. */
export type AreaType = "platform" | "concourse";

/** One patrol area (station level) as the stream sends it. */
export interface Area {
  /** Unique within its station. */
  area_id: string;
  name: string;
  /** Metro lines the area serves, e.g. ["M1", "M2"] at an interchange. */
  line: string[];
  area_type: AreaType;
  /** True while a steward is patrolling the area right now. */
  covered_now: boolean;
  /**
   * When the area becomes (or became) overdue, ISO 8601 date-time with offset.
   * Null while the area is covered now or when it has never been patrolled.
   */
  overdue_at: string | null;
}

/** A station with its patrol areas, in the order the backend sends them. */
export interface Station {
  /** Stable identifier from the station dataset. */
  station_id: string;
  name: string;
  areas: Area[];
}

/**
 * Manning totals and current stewards of one train.
 *
 * The share of time a train was manned is `manned_time_secs / total_time_secs`.
 */
export interface Train {
  /** UUID of the train. */
  train_id: string;
  /** Human-readable identifier for the train. */
  slug: string;
  /** Seconds since the train started being tracked. */
  total_time_secs: number;
  /** Seconds of that time the train was manned by a steward. */
  manned_time_secs: number;
  /** UUIDs of stewards currently manning the train; empty when unmanned. */
  current_steward_ids: string[];
  /** Metro lines the train serves, e.g. ["M1", "M2"] (position-interface v2.4.0). */
  line: string[];
}

/**
 * One `dashboard` event. It contains every station, changed or not, so it
 * replaces the whole previous state. Trains arrive on the trains stream.
 */
export interface Dashboard {
  stations: Station[];
  /** When the server sent the event, ISO 8601 date-time with offset. */
  time: string;
}

/**
 * One `trains` event. It contains every train, changed or not, so it replaces
 * the whole previous state.
 */
export interface TrainsUpdate {
  trains: Train[];
  /** Manned-time ratio 0..1 over all trains; null when there is no running time. */
  manning_percent: number | null;
  /** Same ratio over trains whose line contains M1 or M2. */
  m1m2_manning_percent: number | null;
  /** Same ratio over trains whose line contains M3 or M4. */
  m3m4_manning_percent: number | null;
  /** When the server sent the event, ISO 8601 date-time with offset. */
  time: string;
}

/** Body of an error response, the contract's Error schema. */
export interface ApiError {
  /** Machine-readable error code. */
  code: string;
  /** Human-readable message meant for developers. */
  message: string;
}

/**
 * Open a bare EventSource on the dashboard stream.
 *
 * No listeners are attached: the caller handles the `dashboard` events and
 * must call `.close()` when done. {@link subscribeToDashboard} does both the
 * opening and the parsing.
 */
export function connectDashboardStream(): EventSource {
  return new EventSource(`${API_BASE_URL}${API_VERSION}/dashboard/stream`);
}

/**
 * Open the dashboard stream and call `callback` with each parsed event.
 *
 * Only events named `dashboard` are handled. A payload that is not valid JSON
 * is logged with `console.error` and skipped; valid JSON is passed on without
 * checking it against the contract. Reconnecting is left to the browser, which
 * retries a dropped connection by itself but gives up for good when the server
 * answers with an HTTP error.
 *
 * @param onError - Set as the EventSource's `onerror`. It receives a plain
 *   Event with no message, on every failed connection attempt.
 * @returns The EventSource; call `.close()` to disconnect.
 */
export function subscribeToDashboard(
  callback: (dashboard: Dashboard) => void,
  onError?: (error: Event) => void
): EventSource {
  const eventSource = new EventSource(`${API_BASE_URL}${API_VERSION}/dashboard/stream`);

  eventSource.addEventListener("dashboard", (event) => {
    try {
      const dashboard: Dashboard = JSON.parse(event.data);
      callback(dashboard);
    } catch (error) {
      console.error("Failed to parse dashboard event:", error);
    }
  });

  if (onError) {
    eventSource.onerror = onError;
  }

  return eventSource;
}

/**
 * Open a bare EventSource on the trains stream.
 *
 * No listeners are attached: the caller handles the `trains` events and must
 * call `.close()` when done. {@link subscribeToTrains} does both the opening
 * and the parsing.
 */
export function connectTrainsStream(): EventSource {
  return new EventSource(`${API_BASE_URL}${API_VERSION}/trains/stream`);
}

/**
 * Open the trains stream and call `callback` with each parsed event.
 *
 * Only events named `trains` are handled. A payload that is not valid JSON is
 * logged with `console.error` and skipped; valid JSON is passed on without
 * checking it against the contract. Reconnecting is left to the browser.
 *
 * @param onError - Set as the EventSource's `onerror`. It receives a plain
 *   Event with no message, on every failed connection attempt.
 * @returns The EventSource; call `.close()` to disconnect.
 */
export function subscribeToTrains(
  callback: (update: TrainsUpdate) => void,
  onError?: (error: Event) => void
): EventSource {
  const eventSource = new EventSource(`${API_BASE_URL}${API_VERSION}/trains/stream`);

  eventSource.addEventListener("trains", (event) => {
    try {
      const update: TrainsUpdate = JSON.parse(event.data);
      callback(update);
    } catch (error) {
      console.error("Failed to parse trains event:", error);
    }
  });

  if (onError) {
    eventSource.onerror = onError;
  }

  return eventSource;
}
