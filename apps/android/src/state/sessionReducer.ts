// decides the next session state. pure: no requests, timers or other side effects.
// the start time comes in with START_REQUESTED, so the reducer never reads the clock itself.
//
// action           only when status is   new status   error     startedAt
// START_REQUESTED  stopped               starting     null      from action
// START_SUCCEEDED  starting              active       null      kept
// START_FAILED     starting              stopped      message   null
// STOP_REQUESTED   active                stopping     null      kept
// STOP_SUCCEEDED   stopping              stopped      null      null
// STOP_FAILED      stopping              active       message   kept
//
// any other combination (double-taps, late responses) is ignored and returns the same state.
import type { PatrolSessionAction, PatrolSessionState } from "@/types/patrol_session/patrolSession";

export function sessionReducer(state: PatrolSessionState, action: PatrolSessionAction): PatrolSessionState {
  switch (action.type) {
    case "START_REQUESTED":
      if (state.status !== "stopped") return state;
      return { status: "starting", error: null, startedAt: action.startedAt };

    case "START_SUCCEEDED":
      if (state.status !== "starting") return state;
      return { status: "active", error: null, startedAt: state.startedAt };

    case "START_FAILED":
      if (state.status !== "starting") return state;
      return { status: "stopped", error: action.error, startedAt: null };

    case "STOP_REQUESTED":
      if (state.status !== "active") return state;
      return { status: "stopping", error: null, startedAt: state.startedAt };

    case "STOP_SUCCEEDED":
      if (state.status !== "stopping") return state;
      return { status: "stopped", error: null, startedAt: null };

    case "STOP_FAILED":
      if (state.status !== "stopping") return state;
      return { status: "active", error: action.error, startedAt: state.startedAt };

    default: {
      // if a new action is added to SessionAction without a case above, this line fails to compile
      const unhandled: never = action;
      throw new Error(`Unknown session action: ${JSON.stringify(unhandled)}`);
    }
  }
}
