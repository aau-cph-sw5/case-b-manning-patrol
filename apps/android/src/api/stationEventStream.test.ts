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
    options: { headers?: Record<string, string> } | undefined;
    listeners: Record<string, Listener[]> = {};
    closed = false;

    constructor(url: string, options?: { headers?: Record<string, string> }) {
      this.url = url;
      this.options = options;
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

const { getAccessToken } = vi.hoisted(() => ({ getAccessToken: vi.fn() }));

vi.mock("@/api/auth", () => ({ getAccessToken }));


const validPayload = JSON.stringify({
  stations: [
    {
      station_id: "vanlose",
      name: "Vanløse",
      areas: [
        {
          area_id: "platform-1",
          name: "Perron 1",
          line: ["M1", "M2"],
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

async function connect() {
  const onUpdate = vi.fn();
  const onError = vi.fn();
  const disconnect = connectToStationUpdates(onUpdate, onError);
  await vi.waitFor(() => expect(instances).toHaveLength(1));
  const source = instances[0];
  return { onUpdate, onError, disconnect, source };
}

beforeEach(() => {
  instances.length = 0;
  getAccessToken.mockReset().mockResolvedValue("test-token");
});

describe("connectToStationUpdates", () => {
  it("opens one stream per call with open, dashboard and error handlers", async () => {
    const { source } = await connect();

    expect(instances).toHaveLength(1);
    expect(source.url).toBe("http://localhost:8000/api/v2/dashboard/stream");
    expect(Object.keys(source.listeners).sort()).toEqual([
      "dashboard",
      "error",
      "open",
    ]);
  });

  it("delivers a valid payload to onUpdate with overdueAt as a Date", async () => {
    const { onUpdate, onError, source } = await connect();

    source.listeners["dashboard"][0]({ data: validPayload });

    expect(onUpdate).toHaveBeenCalledTimes(1);
    const [overview] = onUpdate.mock.calls[0];
    expect(overview.stations).toHaveLength(1);
    expect(overview.stations[0].name).toBe("Vanløse");
    expect(overview.stations[0].areas[0].overdueAt).toEqual(
      new Date("2026-10-23T10:00:00.000Z"),
    );
    expect(overview.stations[0].areas[0].line).toEqual(["M1", "M2"]);
    expect(onError).not.toHaveBeenCalled();
  });

  it("delivers each message as its own snapshot", async () => {
    const { onUpdate, source } = await connect();

    source.listeners["dashboard"][0]({ data: validPayload });
    source.listeners["dashboard"][0]({ data: validPayload });

    expect(onUpdate).toHaveBeenCalledTimes(2);
  });

  it("ignores messages without data", async () => {
    const { onUpdate, onError, source } = await connect();

    source.listeners["dashboard"][0]({ data: null });

    expect(onUpdate).not.toHaveBeenCalled();
    expect(onError).not.toHaveBeenCalled();
  });

  it("routes a malformed payload to onError instead of onUpdate", async () => {
    const { onUpdate, onError, source } = await connect();

    source.listeners["dashboard"][0]({
      data: JSON.stringify({ stations: [{ areas: [] }] }),
    });

    expect(onUpdate).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledTimes(1);
  });

  it("routes a non-JSON payload to onError", async () => {
    const { onUpdate, onError, source } = await connect();

    source.listeners["dashboard"][0]({ data: "not json" });

    expect(onUpdate).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledTimes(1);
  });

  it("routes stream errors to onError with the event", async () => {
    const { onError, source } = await connect();
    const event = { data: null };

    source.listeners["error"][0](event);

    expect(onError).toHaveBeenCalledTimes(1);
    expect(onError.mock.calls[0][0]).toBe(event);
  });

  it("closes the stream from the returned disconnect", async () => {
    const { disconnect, source } = await connect();

    expect(source.closed).toBe(false);
    disconnect();

    expect(source.closed).toBe(true);
  });

  it("sends the access token as a bearer Authorization header", async () => {
    const { source } = await connect();

    expect(source.options?.headers).toEqual({ Authorization: "Bearer test-token" });
  });

  it("opens no stream when disconnected before the token arrives", async () => {
    let resolveToken: (token: string) => void = () => {};
    getAccessToken.mockReturnValue(
      new Promise<string>((resolve) => {
        resolveToken = resolve;
      }),
    );

    const disconnect = connectToStationUpdates(vi.fn(), vi.fn());
    disconnect();
    resolveToken("test-token");
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(instances).toHaveLength(0);
  });

  it("routes a failure to get the token to onError", async () => {
    const failure = new Error("no token");
    getAccessToken.mockRejectedValue(failure);
    const onError = vi.fn();

    connectToStationUpdates(vi.fn(), onError);

    await vi.waitFor(() => expect(onError).toHaveBeenCalledWith(failure));
    expect(instances).toHaveLength(0);
  });
});
