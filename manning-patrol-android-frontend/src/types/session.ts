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
