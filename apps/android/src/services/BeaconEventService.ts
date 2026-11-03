/** Turns a scanner's raw beacon events into confirmed connections and disconnections. */
import type { BeaconConnectionEvent } from "@/types/beacon";

/** Timing for {@link BeaconEventService}. */
export type BeaconEventServiceOptions = {
  /** How long a beacon must stay connected before its CONNECTED is forwarded. Defaults to 3000. */
  minimumConnectionDurationMs?: number;
  /** How long a DISCONNECTED waits for a reconnect before it is forwarded. Defaults to 10000. */
  disconnectConfirmationDelayMs?: number;
};

type BeaconConnectionState = {
  connectionEvent: BeaconConnectionEvent;
  /** True once the connection lasted the minimum duration and was forwarded. */
  isQualified: boolean;
  qualificationTimer: ReturnType<typeof setTimeout> | null;
  pendingDisconnectEvent: BeaconConnectionEvent | null;
  disconnectTimer: ReturnType<typeof setTimeout> | null;
};

const MINIMUM_CONNECTION_DURATION_MS = 3_000;
const DISCONNECT_CONFIRMATION_DELAY_MS = 10_000;

/**
 * Filter raw scanner events, per beacon, down to the ones worth reporting.
 *
 * A CONNECTED is forwarded only once the beacon has stayed connected for the
 * minimum duration; a disconnect before that drops the connection silently.
 * A DISCONNECTED of a forwarded connection is held for the confirmation delay
 * and forwarded, with its original timestamp, only if the beacon does not
 * reconnect meanwhile. Repeated CONNECTED events for a known beacon and
 * DISCONNECTED events for an unknown one are ignored.
 *
 * Runs timers; call {@link BeaconEventService.reset} when scanning stops.
 */
export class BeaconEventService {
  private readonly connections = new Map<string, BeaconConnectionState>();
  private readonly minimumConnectionDurationMs: number;
  private readonly disconnectConfirmationDelayMs: number;

  /**
   * Create a service that forwards confirmed events.
   *
   * @param forwardEvent - Called from a timer callback with each confirmed event.
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

  /** Feed in one raw scanner event. Anything forwarded is forwarded later, from a timer. */
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

  /** Cancel every pending confirmation and forget all beacons, forwarding nothing. */
  reset(): void {
    for (const connection of this.connections.values()) {
      this.clearTimer(connection.qualificationTimer);
      this.clearTimer(connection.disconnectTimer);
    }
    this.connections.clear();
  }

  /** Cancel a pending disconnect of a known beacon, or start qualifying a new one. */
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