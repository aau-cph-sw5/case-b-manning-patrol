// "starting" and "stopping" mean a request is in flight; the button should be disabled.
export type SessionStatus = "stopped" | "starting" | "active" | "stopping";

export type SessionState = {
  status: SessionStatus;
  // set when the last start/stop request failed. the status rolls back to what is still true
  // (a failed start stays "stopped", a failed stop stays "active").
  error: string | null;
  // device time (ms since epoch) when the current session was confirmed as started, null otherwise.
  // taken at confirmation, not at the press, so the timer starts at 00:00:00 when it appears.
  startedAt: number | null;
};

export const initialSessionState: SessionState = {
  status: "stopped",
  error: null,
  startedAt: null,
};

// things that happened to the session. a confirmed start carries the moment it was confirmed,
// failures carry the message to show.
export type SessionAction =
  | { type: "START_REQUESTED" }
  | { type: "START_SUCCEEDED"; startedAt: number }
  | { type: "START_FAILED"; error: string }
  | { type: "STOP_REQUESTED" }
  | { type: "STOP_SUCCEEDED" }
  | { type: "STOP_FAILED"; error: string };
