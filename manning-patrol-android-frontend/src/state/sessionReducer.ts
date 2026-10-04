// decides the next session state. pure: no requests, timers or other side effects.
//
// action           only when status is   new status   error
// START_REQUESTED  stopped               starting     null
// START_SUCCEEDED  starting              active       null
// START_FAILED     starting              stopped      message
// STOP_REQUESTED   active                stopping     null
// STOP_SUCCEEDED   stopping              stopped      null
// STOP_FAILED      stopping              active       message
//
// any other combination (double-taps, late responses) is ignored and returns the same state.
import type { SessionAction, SessionState } from "@/types/session";

export function sessionReducer(state: SessionState, action: SessionAction): SessionState {
  switch (action.type) {
    case "START_REQUESTED":
      if (state.status !== "stopped") return state;
      return { status: "starting", error: null };

    case "START_SUCCEEDED":
      if (state.status !== "starting") return state;
      return { status: "active", error: null };

    case "START_FAILED":
      if (state.status !== "starting") return state;
      return { status: "stopped", error: action.error };

    case "STOP_REQUESTED":
      if (state.status !== "active") return state;
      return { status: "stopping", error: null };

    case "STOP_SUCCEEDED":
      if (state.status !== "stopping") return state;
      return { status: "stopped", error: null };

    case "STOP_FAILED":
      if (state.status !== "stopping") return state;
      return { status: "active", error: action.error };

    default: {
      // if a new action is added to SessionAction without a case above, this line fails to compile
      const unhandled: never = action;
      throw new Error(`Unknown session action: ${JSON.stringify(unhandled)}`);
    }
  }
}
