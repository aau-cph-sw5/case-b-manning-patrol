/**
 * Client for the dashboard SSE stream, `GET /api/v2/dashboard/stream`
 * (contracts/api/v2/positioning-interface), served by the same API as the POST
 * endpoints.
 *
 * The stream sends two event types: `dashboard` with the station snapshot and
 * `at-risk-threshold` with the current at-risk threshold, so the app can
 * re-colour stations when the threshold is changed from the control room.
 *
 * Uses react-native-sse in every runtime, the browser included: it is plain
 * JavaScript over XMLHttpRequest and, unlike the browser's native
 * `EventSource`, can send an `Authorization` header. Every payload is
 * validated before it is handed on.
 */
import EventSource from "react-native-sse";

import { AtRiskThresholdSchema, type AtRiskThreshold } from "@/types/config";
import { StationOverviewSchema, type StationOverview } from "@/types/station";

import { getAccessToken } from "@/fixtures/auth";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

const SSE_URL = `${API_BASE_URL}/api/v2/dashboard/stream`;

/** Callbacks for the events the dashboard stream sends. */
export type StationStreamHandlers = {
  /** Receives every `dashboard` event whose data parses and passes validation. */
  onStations: (overview: StationOverview) => void;
  /** Receives every `at-risk-threshold` event whose data parses and passes validation. */
  onAtRiskThreshold: (threshold: AtRiskThreshold) => void;
  /** Receives connection errors and payloads that fail parsing or validation. */
  onError: (error: unknown) => void;
};

/**
 * Subscribe to the dashboard stream and deliver each validated event.
 *
 * `onStations` receives every `dashboard` event and `onAtRiskThreshold` every
 * `at-risk-threshold` event whose data parses as JSON and passes its schema;
 * events without data are skipped. `onError` receives both connection errors
 * (the raw error event) and payloads that fail parsing or validation (the
 * thrown error). An error does not close the connection: reconnecting is left
 * to react-native-sse, and this module adds no retry of its own.
 *
 * The stream sends `Authorization: Bearer <token>` from {@link getAccessToken}
 * and opens asynchronously once the token is ready; a failure to get the token
 * goes to `onError`. Disconnecting before the token arrives cancels the
 * connection, so no stream is opened at all.
 *
 * @returns A function that closes the connection; call it on unmount.
 */
export function connectToStationUpdates(handlers: StationStreamHandlers) {
  let source: EventSource<"dashboard" | "at-risk-threshold"> | null = null;
  let closed = false;

  getAccessToken()
    .then((token) => {
      if (closed) {
        return;
      }
      // the type parameter names the custom events the backend sends, so the
      // listeners receive them with a typed data field.
      source = new EventSource<"dashboard" | "at-risk-threshold">(SSE_URL, {
        headers: { Authorization: `Bearer ${token}` },
      });

      source.addEventListener("open", () => {
        console.log("SSE connection opened");
      });

      source.addEventListener("dashboard", (event) => {
        if (event.data === null) {
          return;
        }
        deliver(event.data, StationOverviewSchema, handlers.onStations, handlers.onError);
      });

      source.addEventListener("at-risk-threshold", (event) => {
        if (event.data === null) {
          return;
        }
        deliver(event.data, AtRiskThresholdSchema, handlers.onAtRiskThreshold, handlers.onError);
      });

      source.addEventListener("error", (event) => {
        handlers.onError(event);
      });
    })
    .catch(handlers.onError);

  return () => {
    closed = true;
    source?.close();
  };
}

/**
 * Parse one raw event payload and route it.
 *
 * SSE delivers `event.data` as a raw JSON string, so it is parsed before zod:
 * valid payloads reach `onValid`, failures route to `onError`.
 */
function deliver<T>(
  data: string,
  schema: { parse: (input: unknown) => T },
  onValid: (value: T) => void,
  onError: (error: unknown) => void,
) {
  try {
    onValid(schema.parse(JSON.parse(data)));
  } catch (error) {
    onError(error);
  }
}
