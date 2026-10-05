// the session state machine, one case per row that matters: start, stop and the
// rollbacks. combinations outside the table are ignored.
import { describe, expect, it } from "vitest";

import { sessionReducer } from "@/state/sessionReducer";
import { initialSessionState } from "@/types/session";

const startedAt = 1760000000000;

describe("sessionReducer", () => {
  it("moves stopped -> starting -> active on a successful start", () => {
    let state = sessionReducer(initialSessionState, { type: "START_REQUESTED", startedAt });
    expect(state).toEqual({ status: "starting", error: null, startedAt });

    state = sessionReducer(state, { type: "START_SUCCEEDED" });
    expect(state).toEqual({ status: "active", error: null, startedAt });
  });

  it("rolls back to stopped with an error when the start fails", () => {
    let state = sessionReducer(initialSessionState, { type: "START_REQUESTED", startedAt });
    state = sessionReducer(state, { type: "START_FAILED", error: "network" });
    expect(state).toEqual({ status: "stopped", error: "network", startedAt: null });
  });

  it("ignores a second start while one is already in flight", () => {
    const state = sessionReducer(initialSessionState, { type: "START_REQUESTED", startedAt });
    const doubleTap = sessionReducer(state, { type: "START_REQUESTED", startedAt: startedAt + 1 });
    expect(doubleTap).toBe(state);
  });

  it("moves active -> stopping -> stopped on a successful stop and forgets startedAt", () => {
    let state = sessionReducer(initialSessionState, { type: "START_REQUESTED", startedAt });
    state = sessionReducer(state, { type: "START_SUCCEEDED" });

    state = sessionReducer(state, { type: "STOP_REQUESTED" });
    expect(state.status).toBe("stopping");

    state = sessionReducer(state, { type: "STOP_SUCCEEDED" });
    expect(state).toEqual({ status: "stopped", error: null, startedAt: null });
  });

  it("stays active with an error when the stop fails", () => {
    let state = sessionReducer(initialSessionState, { type: "START_REQUESTED", startedAt });
    state = sessionReducer(state, { type: "START_SUCCEEDED" });
    state = sessionReducer(state, { type: "STOP_REQUESTED" });
    state = sessionReducer(state, { type: "STOP_FAILED", error: "network" });
    expect(state).toEqual({ status: "active", error: "network", startedAt });
  });
});
