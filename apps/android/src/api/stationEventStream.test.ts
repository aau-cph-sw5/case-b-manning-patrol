// pins the SSE boundary contract: schema-valid payloads reach onUpdate with
// overdueAt coerced to Date, malformed or empty data routes to onError, and
// the returned function closes the stream. the EventSource is a fake, so these
// tests run in the plain node environment with no react-native involved.
import { beforeEach, describe, expect, it, vi } from "vitest";

import { connectToStationUpdates } from "@/api/stationEventStream";

type Listener = (event: { data: string | null }) => void;

const { MockEventSource, instances } = vi.hoisted(() => {
  class MockEventSource {
    static instances: MockEventSource[] = [];
    url: string;
    listeners: Record<string, Listener[]> = {};
    closed = false;

    constructor(url: string) {
      this.url = url;
      MockEventSource.instances.push(this);
    }

    addEventListener(type: string, listener: Listener) {
      (this.listeners[type] ??= []).push(listener);
    }

    close() {
      this.closed = true;
    }
  }
  return { MockEventSource, instances: MockEventSource.instances };
});

vi.mock("react-native-sse", () => ({ default: MockEventSource }));


const validPayload = JSON.stringify({
  stations: [
    {
      station_id: "vanlose",
      name: "Vanløse",
      areas: [
        {
          area_id: "platform-1",
          name: "Perron 1",
          line: "M1",
          area_type: "platform",
          covered_now: false,
          overdue_at: "2026-10-23T10:00:00.000Z",
        },
      ],
    },
  ],
  trains: [],
  time: "2026-10-23T09:59:00.000Z",
});

function connect() {
  const onUpdate = vi.fn();
  const onError = vi.fn();
  const disconnect = connectToStationUpdates(onUpdate, onError);
  const source = instances[0];
  return { onUpdate, onError, disconnect, source };
}

beforeEach(() => {
  instances.length = 0;
});

describe("connectToStationUpdates", () => {
  it("opens one stream per call with open, dashboard and error handlers", () => {
    const { source } = connect();

    expect(instances).toHaveLength(1);
    expect(source.url).toBe("http://localhost:8000/api/v2/dashboard/stream");
    expect(Object.keys(source.listeners).sort()).toEqual([
      "dashboard",
      "error",
      "open",
    ]);
  });

  it("delivers a valid payload to onUpdate with overdueAt as a Date", () => {
    const { onUpdate, onError, source } = connect();

    source.listeners["dashboard"][0]({ data: validPayload });

    expect(onUpdate).toHaveBeenCalledTimes(1);
    const [overview] = onUpdate.mock.calls[0];
    expect(overview.stations).toHaveLength(1);
    expect(overview.stations[0].name).toBe("Vanløse");
    expect(overview.stations[0].areas[0].overdueAt).toEqual(
      new Date("2026-10-23T10:00:00.000Z"),
    );
    expect(onError).not.toHaveBeenCalled();
  });

  it("delivers each message as its own snapshot", () => {
    const { onUpdate, source } = connect();

    source.listeners["dashboard"][0]({ data: validPayload });
    source.listeners["dashboard"][0]({ data: validPayload });

    expect(onUpdate).toHaveBeenCalledTimes(2);
  });

  it("ignores messages without data", () => {
    const { onUpdate, onError, source } = connect();

    source.listeners["dashboard"][0]({ data: null });

    expect(onUpdate).not.toHaveBeenCalled();
    expect(onError).not.toHaveBeenCalled();
  });

  it("routes a malformed payload to onError instead of onUpdate", () => {
    const { onUpdate, onError, source } = connect();

    source.listeners["dashboard"][0]({
      data: JSON.stringify({ stations: [{ areas: [] }] }),
    });

    expect(onUpdate).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledTimes(1);
  });

  it("routes a non-JSON payload to onError", () => {
    const { onUpdate, onError, source } = connect();

    source.listeners["dashboard"][0]({ data: "not json" });

    expect(onUpdate).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledTimes(1);
  });

  it("routes stream errors to onError with the event", () => {
    const { onError, source } = connect();
    const event = { data: null };

    source.listeners["error"][0](event);

    expect(onError).toHaveBeenCalledTimes(1);
    expect(onError.mock.calls[0][0]).toBe(event);
  });

  it("closes the stream from the returned disconnect", () => {
    const { disconnect, source } = connect();

    expect(source.closed).toBe(false);
    disconnect();

    expect(source.closed).toBe(true);
  });
});
