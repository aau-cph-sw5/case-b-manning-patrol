import type { BeaconConnectionEvent } from "@/types/beacon";

export type BeaconEventServiceOptions = {
  minimumConnectionDurationMs?: number;
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

export class BeaconEventService {
  private readonly connections = new Map<string, BeaconConnectionState>();
  private readonly minimumConnectionDurationMs: number;
  private readonly disconnectConfirmationDelayMs: number;

  constructor(
    private readonly forwardEvent: (event: BeaconConnectionEvent) => void,
    options: BeaconEventServiceOptions = {},
  ) {
    this.minimumConnectionDurationMs =
      options.minimumConnectionDurationMs ?? MINIMUM_CONNECTION_DURATION_MS;
    this.disconnectConfirmationDelayMs =
      options.disconnectConfirmationDelayMs ?? DISCONNECT_CONFIRMATION_DELAY_MS;
  }

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