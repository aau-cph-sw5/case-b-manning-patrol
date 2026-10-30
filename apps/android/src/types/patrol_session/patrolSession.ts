/** Where a patrol session is. "starting" and "stopping" mean a request is in flight; the slider is locked. */
export type PatrolSessionStatus = "stopped" | "starting" | "active" | "stopping";

/** A steward's patrol session as the app sees it. */
export type PatrolSessionState = {
  status: PatrolSessionStatus;
  /**
   * Set when the last start/stop request failed. The status rolls back to
   * what is still true (a failed start stays "stopped", a failed stop stays
   * "active").
   */
  error: string | null;
  /**
   * Device time (ms since epoch) when the steward started the current
   * session, null when stopped. The phone is the source of truth for event
   * time (ADR-0004).
   */
  startedAt: number | null;
};

export const initialSessionState: PatrolSessionState = {
  status: "stopped",
  error: null,
  startedAt: null,
};

/**
 * Things that happened to the session. A start request carries the moment the
 * steward started it, failures carry the message to show.
 */
export type PatrolSessionAction =
  | { type: "START_REQUESTED"; startedAt: number }
  | { type: "START_SUCCEEDED" }
  | { type: "START_FAILED"; error: string }
  | { type: "STOP_REQUESTED" }
  | { type: "STOP_SUCCEEDED" }
  | { type: "STOP_FAILED"; error: string };
