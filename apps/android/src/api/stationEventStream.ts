import EventSource from "react-native-sse";
import { StationOverviewSchema, type StationOverview } from "@/types/station";

// the dashboard stream of the positioning-interface contract, served by the
// same API as the POST endpoints.
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";
const SSE_URL = `${API_BASE_URL}/api/v2/dashboard/stream`;

// browsers ship SSE support natively; react-native-sse fills the gap in the
// react-native runtimes. in react-native `window` exists but `window.EventSource`
// does not, which tells the browser apart from the react-native runtimes (and
// from the node test environment, where neither exists).
const BROWSER_EVENT_SOURCE =
  typeof window !== "undefined" && typeof window.EventSource !== "undefined";

type OnUpdate = (data: StationOverview) => void;
type OnError = (error: unknown) => void;

//Connection to SSE with actions acceptable are open, dashboard and error
export function connectToStationUpdates(onUpdate: OnUpdate, onError: OnError) {
  return BROWSER_EVENT_SOURCE
    ? connectInBrowser(onUpdate, onError)
    : connectInReactNative(onUpdate, onError);
}

// SSE delivers event.data as a raw JSON string, so parse before zod: valid
// payloads reach onUpdate, failures route to onError.
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
