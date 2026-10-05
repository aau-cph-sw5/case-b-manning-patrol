// "starting" and "stopping" mean a request is in flight; the button should be disabled.
export type SessionStatus = "stopped" | "starting" | "active" | "stopping";

export type SessionState = {
  status: SessionStatus;
  // set when the last start/stop request failed. the status rolls back to what is still true
  // (a failed start stays "stopped", a failed stop stays "active").
  error: string | null;
  // device time (ms since epoch) when the steward started the current session, null when stopped.
  // the phone is the source of truth for event time (ADR-0004).
  startedAt: number | null;
};

export const initialSessionState: SessionState = {
  status: "stopped",
  error: null,
  startedAt: null,
};

// things that happened to the session. a start request carries the moment the steward started it,
// failures carry the message to show.
export type SessionAction =
  | { type: "START_REQUESTED"; startedAt: number }
  | { type: "START_SUCCEEDED" }
  | { type: "START_FAILED"; error: string }
  | { type: "STOP_REQUESTED" }
  | { type: "STOP_SUCCEEDED" }
  | { type: "STOP_FAILED"; error: string };
