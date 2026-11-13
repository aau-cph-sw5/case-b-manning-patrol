/**
 * Types and clients for the dashboard and trains Server-Sent Events streams,
 * `GET /api/v2/dashboard/stream` and `GET /api/v2/trains/stream`
 * (position-interface/v2 contract).
 *
 * The backend URL comes from `VITE_API_URL` and defaults to
 * http://localhost:8000.
 */
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { getAccessToken } from "@/api/auth";

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
 * One train and the stewards on it right now.
 *
 * Per-train manned time is not exposed (position-interface v2.4.0); use the
 * percentages on {@link TrainsUpdate}.
 */
export interface Train {
  /** UUID of the train. */
  train_id: string;
  /** Human-readable identifier for the train. */
  slug: string;
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
  /**
   * Manning percentage 0..100 over all trains (position-interface v2.5.0);
   * null when there is no running time.
   */
  manning_percent: number | null;
  /** Same percentage over trains whose line contains M1 or M2. */
  m1m2_manning_percent: number | null;
  /** Same percentage over trains whose line contains M3 or M4. */
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
 * Open an authenticated stream and call `callback` with each parsed `eventName` event.
 *
 * Uses fetch-event-source instead of the browser's EventSource, which cannot
 * send headers: every connection attempt sends `Authorization: Bearer <token>`
 * from {@link getAccessToken}. It keeps retrying, one second apart unless the
 * server sends a `retry:` field, after a dropped connection, an HTTP error, or
 * the server ending the stream. It stays connected while the tab is hidden.
 * Disconnecting before the token arrives opens no stream at all.
 *
 * A payload that is not valid JSON is logged with `console.error` and skipped;
 * valid JSON is passed on without checking it against the contract.
 *
 * @param onError - Called on every failed connection attempt, and when the
 *   token cannot be got, with the underlying error.
 * @returns A function that closes the stream and stops retrying.
 */
function subscribeToStream<T>(
  path: string,
  eventName: string,
  callback: (data: T) => void,
  onError?: (error: unknown) => void
): () => void {
  const controller = new AbortController();

  getAccessToken()
    .then((token) => {
      if (controller.signal.aborted) {
        return;
      }
      return fetchEventSource(`${API_BASE_URL}${API_VERSION}${path}`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
        openWhenHidden: true,
        onmessage(message) {
          if (message.event !== eventName) {
            return;
          }
          try {
            callback(JSON.parse(message.data) as T);
          } catch (error) {
            console.error(`Failed to parse ${eventName} event:`, error);
          }
        },
        onclose() {
          // fetch-event-source only retries on a thrown error; a stream the
          // server ends would otherwise stay closed for good.
          throw new Error(`The server closed the ${eventName} stream`);
        },
        onerror(error) {
          onError?.(error);
        },
      });
    })
    .catch((error: unknown) => onError?.(error));

  return () => controller.abort();
}

/**
 * Open the dashboard stream and call `callback` with each parsed `dashboard` event.
 *
 * See {@link subscribeToStream} for authentication, reconnecting and errors.
 *
 * @returns A function that closes the stream; call it on unmount.
 */
export function subscribeToDashboard(
  callback: (dashboard: Dashboard) => void,
  onError?: (error: unknown) => void
): () => void {
  return subscribeToStream("/dashboard/stream", "dashboard", callback, onError);
}

/**
 * Open the trains stream and call `callback` with each parsed `trains` event.
 *
 * See {@link subscribeToStream} for authentication, reconnecting and errors.
 *
 * @returns A function that closes the stream; call it on unmount.
 */
export function subscribeToTrains(
  callback: (update: TrainsUpdate) => void,
  onError?: (error: unknown) => void
): () => void {
  return subscribeToStream("/trains/stream", "trains", callback, onError);
}
