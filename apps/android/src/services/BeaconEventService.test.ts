import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { BeaconEventService } from "@/services/BeaconEventService";
import type { BeaconConnectionEvent } from "@/types/beacon";

const CONNECTION_QUALIFICATION_MS = 3_000;
const DISCONNECT_CONFIRMATION_MS = 10_000;

function beaconEvent(
  event: BeaconConnectionEvent["event"],
  timestamp: string,
): BeaconConnectionEvent {
  return { event, beacon_id: "beacon-1", timestamp };
}

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("BeaconEventService", () => {
  it("does not forward a connection that ends before three seconds", () => {
    const forwardedEvents: BeaconConnectionEvent[] = [];
    const service = new BeaconEventService((event) => forwardedEvents.push(event));

    service.handleEvent(beaconEvent("CONNECTED", "2026-10-08T12:00:00.000Z"));
    vi.advanceTimersByTime(CONNECTION_QUALIFICATION_MS - 1);
    service.handleEvent(beaconEvent("DISCONNECTED", "2026-10-08T12:00:02.999Z"));
    vi.advanceTimersByTime(DISCONNECT_CONFIRMATION_MS);

    expect(forwardedEvents).toEqual([]);
  });

  it("forwards a qualified connection with its original event timestamp", () => {
    const forwardedEvents: BeaconConnectionEvent[] = [];
    const service = new BeaconEventService((event) => forwardedEvents.push(event));
    const connectionEvent = beaconEvent("CONNECTED", "2026-10-08T12:00:00.000Z");

    service.handleEvent(connectionEvent);
    vi.advanceTimersByTime(CONNECTION_QUALIFICATION_MS - 1);
    expect(forwardedEvents).toEqual([]);

    vi.advanceTimersByTime(1);
    expect(forwardedEvents).toEqual([connectionEvent]);
  });

  it("waits ten seconds to forward a disconnect and keeps its original timestamp", () => {
    const forwardedEvents: BeaconConnectionEvent[] = [];
    const service = new BeaconEventService((event) => forwardedEvents.push(event));
    const connectionEvent = beaconEvent("CONNECTED", "2026-10-08T12:00:00.000Z");
    const disconnectEvent = beaconEvent("DISCONNECTED", "2026-10-08T12:00:04.000Z");

    service.handleEvent(connectionEvent);
    vi.advanceTimersByTime(CONNECTION_QUALIFICATION_MS);
    service.handleEvent(disconnectEvent);
    vi.advanceTimersByTime(DISCONNECT_CONFIRMATION_MS - 1);

    expect(forwardedEvents).toEqual([connectionEvent]);

    vi.advanceTimersByTime(1);
    expect(forwardedEvents).toEqual([connectionEvent, disconnectEvent]);
  });

  it("suppresses a brief disconnect when the beacon reconnects within ten seconds", () => {
    const forwardedEvents: BeaconConnectionEvent[] = [];
    const service = new BeaconEventService((event) => forwardedEvents.push(event));
    const connectionEvent = beaconEvent("CONNECTED", "2026-10-08T12:00:00.000Z");

    service.handleEvent(connectionEvent);
    vi.advanceTimersByTime(CONNECTION_QUALIFICATION_MS);
    service.handleEvent(beaconEvent("DISCONNECTED", "2026-10-08T12:00:04.000Z"));
    vi.advanceTimersByTime(5_000);
    service.handleEvent(beaconEvent("CONNECTED", "2026-10-08T12:00:09.000Z"));
    vi.advanceTimersByTime(DISCONNECT_CONFIRMATION_MS);

    expect(forwardedEvents).toEqual([connectionEvent]);
  });

  it("cancels an unqualified connection when reset", () => {
    const forwardedEvents: BeaconConnectionEvent[] = [];
    const service = new BeaconEventService((event) => forwardedEvents.push(event));

    service.handleEvent(beaconEvent("CONNECTED", "2026-10-08T12:00:00.000Z"));
    vi.advanceTimersByTime(CONNECTION_QUALIFICATION_MS - 1);
    service.reset();
    vi.advanceTimersByTime(1);

    expect(forwardedEvents).toEqual([]);
  });
});