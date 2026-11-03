/**
 * The patrol session for a screen: its state, and start/stop actions that
 * call the session API.
 *
 * Network code lives in `@/api/postPatrolSessionEvent`, so changing the API
 * does not touch this hook.
 */
import { useReducer, useRef } from "react";

import { startPatrolSession, stopPatrolSession } from "@/api/postPatrolSessionEvent";
import { sessionReducer } from "@/state/sessionReducer";
import { initialSessionState, type PatrolSessionState } from "@/types/patrol_session/patrolSession";

/** Messages shown to the steward. The API's own error message is meant for developers. */
const START_ERROR = "Kunne ikke starte sessionen. Prøv igen.";
const STOP_ERROR = "Kunne ikke stoppe sessionen. Prøv igen.";

/** What {@link usePatrolSession} returns. */
export type UsePatrolSessionResult = {
  state: PatrolSessionState;
  /** Start a stopped session. Does nothing otherwise, or while a request is in flight. */
  start: () => Promise<void>;
  /** Stop an active session. Does nothing otherwise, or while a request is in flight. */
  stop: () => Promise<void>;
};

/**
 * Hold the patrol session state and send start and stop to the backend.
 *
 * `start` records the device time at once (ADR-0004), moves to "starting" and
 * becomes "active" when the backend accepts; `stop` does the same through
 * "stopping". A failed request rolls the status back and sets a message for
 * the steward, so the returned promises never reject. The state lives only in
 * this component and is not restored from the backend after a remount.
 *
 * `startedAt` and the timestamp sent to the backend are read from the clock
 * separately, so they can differ by a few milliseconds.
 */
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
