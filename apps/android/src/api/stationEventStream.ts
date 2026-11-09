/**
 * Client for the dashboard SSE stream, `GET /api/v2/dashboard/stream`
 * (contracts/api/v2/positioning-interface), served by the same API as the POST
 * endpoints.
 *
 * Works in the browser (native `EventSource`) and in the React Native runtimes
 * (react-native-sse), and validates every payload before handing it on.
 */
import EventSource from "react-native-sse";
import { StationOverviewSchema, type StationOverview } from "@/types/station";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";
const SSE_URL = `${API_BASE_URL}/api/v2/dashboard/stream`;

/**
 * True when the runtime ships a native `EventSource`, i.e. in a browser.
 *
 * Browsers support SSE natively; react-native-sse fills the gap in the React
 * Native runtimes. In React Native `window` exists but `window.EventSource`
 * does not, which tells the browser apart from the React Native runtimes (and
 * from the Node test environment, where neither exists).
 */
const BROWSER_EVENT_SOURCE =
  typeof window !== "undefined" && typeof window.EventSource !== "undefined";

type OnUpdate = (data: StationOverview) => void;
type OnError = (error: unknown) => void;

/**
 * Subscribe to the dashboard stream and deliver each validated snapshot.
 *
 * `onUpdate` receives every `dashboard` event whose data parses as JSON and
 * passes {@link StationOverviewSchema}; events without data are skipped.
 * `onError` receives both connection errors (the raw error event) and payloads
 * that fail parsing or validation (the thrown error). An error does not close
 * the connection: reconnecting is left to the EventSource implementation, and
 * this module adds no retry of its own.
 *
 * @returns A function that closes the connection; call it on unmount.
 */
export function connectToStationUpdates(onUpdate: OnUpdate, onError: OnError) {
  return BROWSER_EVENT_SOURCE
    ? connectInBrowser(onUpdate, onError)
    : connectInReactNative(onUpdate, onError);
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

/** Open the stream with react-native-sse; see {@link connectToStationUpdates}. */
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

/** Open the stream with the browser's EventSource; see {@link connectToStationUpdates}. */
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
