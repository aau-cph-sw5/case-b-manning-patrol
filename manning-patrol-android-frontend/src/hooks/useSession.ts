// connects the session state to the start/stop requests. the requests are passed in, so this hook
// contains no network code and works with whatever api implementation it is given.
import { useReducer, useRef } from "react";

import { sessionReducer } from "@/state/sessionReducer";
import { initialSessionState, type SessionState } from "@/types/session";

// shown to the steward. the api's own error message is meant for developers.
const START_ERROR = "Could not start the session. Try again.";
const STOP_ERROR = "Could not stop the session. Try again.";

export type SessionRequests = {
  // each resolves when the server accepted the request, and rejects otherwise
  start: () => Promise<void>;
  stop: () => Promise<void>;
};

export type UseSessionResult = {
  state: SessionState;
  // starts a stopped session or stops an active one. does nothing while a request is in flight.
  toggle: () => Promise<void>;
};

export function useSession({ start, stop }: SessionRequests): UseSessionResult {
  const [state, dispatch] = useReducer(sessionReducer, initialSessionState);
  // a second tap can arrive before the button re-renders as disabled; this stops a second request
  const requestInFlight = useRef(false);

  async function startSession() {
    // the session counts from the moment the steward started it; the phone owns event time (ADR-0004)
    dispatch({ type: "START_REQUESTED", startedAt: Date.now() });
    try {
      await start();
      dispatch({ type: "START_SUCCEEDED" });
    } catch {
      dispatch({ type: "START_FAILED", error: START_ERROR });
    }
  }

  async function stopSession() {
    dispatch({ type: "STOP_REQUESTED" });
    try {
      await stop();
      dispatch({ type: "STOP_SUCCEEDED" });
    } catch {
      dispatch({ type: "STOP_FAILED", error: STOP_ERROR });
    }
  }

  async function toggle() {
    if (requestInFlight.current) return;
    requestInFlight.current = true;
    try {
      if (state.status === "stopped") {
        await startSession();
      } else if (state.status === "active") {
        await stopSession();
      }
    } finally {
      requestInFlight.current = false;
    }
  }

  return { state, toggle };
}
