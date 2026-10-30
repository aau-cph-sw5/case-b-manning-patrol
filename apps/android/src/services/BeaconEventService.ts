import type { BeaconConnectionEvent } from "@/types/beacon";

/** Timing overrides for {@link BeaconEventService}, mainly for tests. */
export type BeaconEventServiceOptions = {
  /** How long a beacon must stay connected before the connect counts. Defaults to 3 s. */
  minimumConnectionDurationMs?: number;
  /** How long a disconnect must last before it counts. Defaults to 10 s. */
  disconnectConfirmationDelayMs?: number;
};

type BeaconConnectionState = {
  connectionEvent: BeaconConnectionEvent;
  isQualified: boolean;
  qualificationTimer: ReturnType<typeof setTimeout> | null;
  pendingDisconnectEvent: BeaconConnectionEvent | null;
  disconnectTimer: ReturnType<typeof setTimeout> | null;
};

const MINIMUM_CONNECTION_DURATION_MS = 3_000;
const DISCONNECT_CONFIRMATION_DELAY_MS = 10_000;

/**
 * Debounce raw scanner events into confirmed connects and disconnects.
 *
 * Tracks each beacon separately and forwards an event only once it holds:
 * - A connect is forwarded after the beacon has stayed connected for the
 *   minimum duration. A disconnect before that drops the connection silently.
 * - A disconnect is forwarded after the confirmation delay, unless the beacon
 *   reconnects first, which cancels it.
 *
 * Forwarded events keep their original timestamp, not the time they were
 * confirmed. Uses timers; call {@link BeaconEventService.reset} to cancel
 * them.
 */
export class BeaconEventService {
  private readonly connections = new Map<string, BeaconConnectionState>();
  private readonly minimumConnectionDurationMs: number;
  private readonly disconnectConfirmationDelayMs: number;

  /**
   * @param forwardEvent - Called once per confirmed event, from a timer
   * callback.
   */
  constructor(
    private readonly forwardEvent: (event: BeaconConnectionEvent) => void,
    options: BeaconEventServiceOptions = {},
  ) {
    this.minimumConnectionDurationMs =
      options.minimumConnectionDurationMs ?? MINIMUM_CONNECTION_DURATION_MS;
    this.disconnectConfirmationDelayMs =
      options.disconnectConfirmationDelayMs ?? DISCONNECT_CONFIRMATION_DELAY_MS;
  }

  /**
   * Feed one raw scanner event in.
   *
   * A connect for a beacon already tracked only cancels its pending
   * disconnect, if any. A disconnect for an untracked beacon and a second
   * disconnect while one is pending are ignored.
   */
  handleEvent(event: BeaconConnectionEvent): void {
    const connection = this.connections.get(event.beacon_id);

    if (event.event === "CONNECTED") {
      this.handleConnected(event, connection);
      return;
    }

    if (connection === undefined) {
      return;
    }

    if (!connection.isQualified) {
      this.clearTimer(connection.qualificationTimer);
      this.connections.delete(event.beacon_id);
      return;
    }

    if (connection.disconnectTimer !== null) {
      return;
    }

    connection.pendingDisconnectEvent = event;
    connection.disconnectTimer = setTimeout(() => {
      this.forwardEvent(event);
      this.connections.delete(event.beacon_id);
    }, this.disconnectConfirmationDelayMs);
  }

  /**
   * Cancel every pending timer and forget all beacons.
   *
   * Pending connects and disconnects are dropped, not forwarded.
   */
  reset(): void {
    for (const connection of this.connections.values()) {
      this.clearTimer(connection.qualificationTimer);
      this.clearTimer(connection.disconnectTimer);
    }
    this.connections.clear();
  }

  private handleConnected(
    event: BeaconConnectionEvent,
    connection: BeaconConnectionState | undefined,
  ): void {
    if (connection !== undefined) {
      if (connection.disconnectTimer !== null) {
        this.clearTimer(connection.disconnectTimer);
        connection.disconnectTimer = null;
        connection.pendingDisconnectEvent = null;
      }
      return;
    }

    const newConnection: BeaconConnectionState = {
      connectionEvent: event,
      isQualified: false,
      qualificationTimer: null,
      pendingDisconnectEvent: null,
      disconnectTimer: null,
    };
    newConnection.qualificationTimer = setTimeout(() => {
      newConnection.isQualified = true;
      newConnection.qualificationTimer = null;
      this.forwardEvent(newConnection.connectionEvent);
    }, this.minimumConnectionDurationMs);
    this.connections.set(event.beacon_id, newConnection);
  }

  private clearTimer(timer: ReturnType<typeof setTimeout> | null): void {
    if (timer !== null) {
      clearTimeout(timer);
    }
  }
}