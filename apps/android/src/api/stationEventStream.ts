import EventSource from "react-native-sse";
import { StationOverviewSchema, type StationOverview } from "@/types/station";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";
/**
 * The dashboard stream of the positioning-interface contract, served by the
 * same API as the POST endpoints.
 */
const SSE_URL = `${API_BASE_URL}/api/v2/dashboard/stream`;

/**
 * Whether the runtime has a native `EventSource`.
 *
 * Browsers ship SSE support natively; react-native-sse fills the gap in the
 * React Native runtimes. In React Native `window` exists but
 * `window.EventSource` does not, which tells the browser apart from the React
 * Native runtimes (and from the node test environment, where neither exists).
 */
const BROWSER_EVENT_SOURCE =
  typeof window !== "undefined" && typeof window.EventSource !== "undefined";

type OnUpdate = (data: StationOverview) => void;
type OnError = (error: unknown) => void;

/**
 * Subscribe to the station overview stream at `/api/v2/dashboard/stream`.
 *
 * Opens the connection immediately. Every `dashboard` event is parsed and
 * validated against {@link StationOverviewSchema}: valid payloads go to
 * `onUpdate`, invalid JSON or schema failures go to `onError`. Connection
 * errors also go to `onError`, once per failed attempt. `open` is only logged.
 *
 * Reconnecting is left to the event source. A browser `EventSource` retries
 * by itself after a network error but gives up on an HTTP error status.
 * react-native-sse re-polls every 5 seconds after the stream ends or the
 * server answers with an error status, but does not retry after a network
 * error.
 *
 * @returns A function that closes the connection; no callbacks fire after it.
 */
export function connectToStationUpdates(onUpdate: OnUpdate, onError: OnError) {
  return BROWSER_EVENT_SOURCE
    ? connectInBrowser(onUpdate, onError)
    : connectInReactNative(onUpdate, onError);
}

/**
 * Parse one raw `dashboard` payload and hand it to the right callback.
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

function connectInReactNative(onUpdate: OnUpdate, onError: OnError) {
  // the type parameter names the custom event the backend sends, so the
  // dashboard listener receives it with a typed data field.
  const source = new EventSource<"dashboard">(SSE_URL);

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

  return () => {
    source.close();
  };
}

function connectInBrowser(onUpdate: OnUpdate, onError: OnError) {
  const source = new window.EventSource(SSE_URL);

  source.addEventListener("open", () => {
    console.log("SSE connection opened");
  });

  source.addEventListener("dashboard", (event) => {
    if (typeof event.data !== "string") {
      return;
    }
    deliver(event.data, onUpdate, onError);
  });

  source.addEventListener("error", (event) => {
    onError(event);
  });

  return () => {
    source.close();
  };
}
