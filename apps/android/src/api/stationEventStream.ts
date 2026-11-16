/**
 * Client for the dashboard SSE stream, `GET /api/v2/dashboard/stream`
 * (contracts/api/v2/positioning-interface), served by the same API as the POST
 * endpoints.
 *
 * Uses react-native-sse in every runtime, the browser included: it is plain
 * JavaScript over XMLHttpRequest and, unlike the browser's native
 * `EventSource`, can send an `Authorization` header. Every payload is
 * validated before it is handed on.
 */
import EventSource from "react-native-sse";
import { StationOverviewSchema, type StationOverview } from "@/types/station";
import { getAccessToken } from "@/api/auth";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";
const SSE_URL = `${API_BASE_URL}/api/v2/dashboard/stream`;

type OnUpdate = (data: StationOverview) => void;
type OnError = (error: unknown) => void;

/**
 * Subscribe to the dashboard stream and deliver each validated snapshot.
 *
 * `onUpdate` receives every `dashboard` event whose data parses as JSON and
 * passes {@link StationOverviewSchema}; events without data are skipped.
 * `onError` receives both connection errors (the raw error event) and payloads
 * that fail parsing or validation (the thrown error). An error does not close
 * the connection: reconnecting is left to react-native-sse, and this module
 * adds no retry of its own.
 *
 * The stream sends `Authorization: Bearer <token>` from {@link getAccessToken}
 * and opens asynchronously once the token is ready; a failure to get the token
 * goes to `onError`. Disconnecting before the token arrives cancels the
 * connection, so no stream is opened at all.
 *
 * @returns A function that closes the connection; call it on unmount.
 */
export function connectToStationUpdates(onUpdate: OnUpdate, onError: OnError) {
  let source: EventSource<"dashboard"> | null = null;
  let closed = false;

  getAccessToken()
    .then((token) => {
      if (closed) {
        return;
      }
      // the type parameter names the custom event the backend sends, so the
      // dashboard listener receives it with a typed data field.
      source = new EventSource<"dashboard">(SSE_URL, {
        headers: { Authorization: `Bearer ${token}` },
      });

      source.addEventListener("open", () => {
        console.log("SSE connection opened");
      });

      source.addEventListener("dashboard", (event) => {
        if (event.data === null) {
          return;
        }
        deliver(event.data, onUpdate, onError);
      });

      source.addEventListener("error", (event) => {
        onError(event);
      });
    })
    .catch(onError);

  return () => {
    closed = true;
    source?.close();
  };
}

/**
 * Parse one raw `dashboard` payload and route it.
 *
 * SSE delivers `event.data` as a raw JSON string, so it is parsed before zod:
 * valid payloads reach `onUpdate`, failures route to `onError`.
 */
function deliver(data: string, onUpdate: OnUpdate, onError: OnError) {
  try {
    onUpdate(StationOverviewSchema.parse(JSON.parse(data)));
  } catch (error) {
    onError(error);
  }
}
