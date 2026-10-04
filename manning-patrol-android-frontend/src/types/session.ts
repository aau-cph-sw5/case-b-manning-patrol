// "starting" and "stopping" mean a request is in flight; the button should be disabled.
export type SessionStatus = "stopped" | "starting" | "active" | "stopping";

export type SessionState = {
  status: SessionStatus;
  // set when the last start/stop request failed. the status rolls back to what is still true
  // (a failed start stays "stopped", a failed stop stays "active").
  error: string | null;
};

export const initialSessionState: SessionState = {
  status: "stopped",
  error: null,
};

// things that happened to the session. only the failures carry data: the message to show.
export type SessionAction =
  | { type: "START_REQUESTED" }
  | { type: "START_SUCCEEDED" }
  | { type: "START_FAILED"; error: string }
  | { type: "STOP_REQUESTED" }
  | { type: "STOP_SUCCEEDED" }
  | { type: "STOP_FAILED"; error: string };
