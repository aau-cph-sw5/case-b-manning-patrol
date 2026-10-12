// the patrol session for a screen: its state, and start/stop actions that call the session api.
// network code lives in @/api/session, so connecting the real api doesn't touch this hook.
import { useReducer, useRef } from "react";

import { startPatrolSession, stopPatrolSession } from "@/api/postPatrolSessionEvent";
import { sessionReducer } from "@/state/sessionReducer";
import { initialSessionState, type PatrolSessionState } from "@/types/patrol_session/patrolSession";

// shown to the steward. the api's own error message is meant for developers.
const START_ERROR = "Could not start the session. Try again.";
const STOP_ERROR = "Could not stop the session. Try again.";

export type UsePatrolSessionResult = {
  state: PatrolSessionState;
  // starts a stopped session. does nothing otherwise, or while a request is in flight.
  start: () => Promise<void>;
  // stops an active session. does nothing otherwise, or while a request is in flight.
  stop: () => Promise<void>;
};

export function usePatrolSession(): UsePatrolSessionResult {
  const [state, dispatch] = useReducer(sessionReducer, initialSessionState);
  // a second slide can complete before the slider re-renders as locked; this stops a second request
  const requestInFlight = useRef(false);

  async function start() {
    if (requestInFlight.current || state.status !== "stopped") return;
    requestInFlight.current = true;
    // the session counts from the moment the steward started it; the phone owns event time (ADR-0004)
    const startedAt = Date.now();
    dispatch({ type: "START_REQUESTED", startedAt });
    try {
      await startPatrolSession(new Date().toISOString());
      dispatch({ type: "START_SUCCEEDED" });
    } catch {
      dispatch({ type: "START_FAILED", error: START_ERROR });
    } finally {
      requestInFlight.current = false;
    }
  }

  async function stop() {
    if (requestInFlight.current || state.status !== "active") return;
    requestInFlight.current = true;
    dispatch({ type: "STOP_REQUESTED" });
    try {
      await stopPatrolSession(new Date().toISOString());
      dispatch({ type: "STOP_SUCCEEDED" });
    } catch {
      dispatch({ type: "STOP_FAILED", error: STOP_ERROR });
    } finally {
      requestInFlight.current = false;
    }
  }

  return { state, start, stop };
}
