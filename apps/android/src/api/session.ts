// the backend requests for starting and stopping a patrol session. this is the only file that knows
// how sessions reach the server; useSession calls it and turns a rejection into the steward's message.
//
// each function resolves once the server has accepted the request and rejects otherwise. it must always
// settle: the slider stays locked on "Starting..." / "Stopping..." until it does, so give requests a timeout.
// times are device time in ms since epoch, since the phone is the source of truth for event time (ADR-0004).
//
// not connected yet: the session endpoints belong to the api ticket. until then both reject, so the
// slider shows the same error a steward would see when the server can't be reached.

export async function startSession(startedAt: number): Promise<void> {
  throw new Error(`Session API not connected: cannot start session at ${startedAt}`);
}

export async function stopSession(stoppedAt: number): Promise<void> {
  throw new Error(`Session API not connected: cannot stop session at ${stoppedAt}`);
}
