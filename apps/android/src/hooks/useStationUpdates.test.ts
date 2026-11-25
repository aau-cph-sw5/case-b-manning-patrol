// pins the contract of the station list hook: the snapshot starts empty with
// the default threshold, a receipt replaces it and stamps the update time, a
// threshold event replaces only the threshold, an error deliberately keeps
// the last state, and unmount disconnects. happy-dom only for the hook
// renderer; the stream connection itself is a mock.
// @vitest-environment happy-dom
import { renderHook, act } from "@testing-library/react";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useStationUpdates } from "@/hooks/useStationUpdates";

import { createMockStations } from "@/fixtures/mockStations";

import { DEFAULT_AT_RISK_THRESHOLD_MINUTES, type AtRiskThreshold } from "@/types/config";
import type { Station, StationOverview } from "@/types/station";

const { connectToStationUpdates, disconnect } = vi.hoisted(() => ({
  connectToStationUpdates: vi.fn(),
  disconnect: vi.fn(),
}));

vi.mock("@/api/stationEventStream", () => ({
  connectToStationUpdates,
}));

const FIXED_NOW = 1760000000000;

let handlers: {
  onStations: (data: StationOverview) => void;
  onAtRiskThreshold: (threshold: AtRiskThreshold) => void;
  onError: (error: unknown) => void;
};

function overview(stations: Station[]): StationOverview {
  return { stations };
}

beforeEach(() => {
  vi.spyOn(Date, "now").mockReturnValue(FIXED_NOW);
  connectToStationUpdates.mockImplementation((h) => {
    handlers = h;
    return disconnect;
  });
});

afterEach(() => {
  vi.restoreAllMocks();
  connectToStationUpdates.mockReset();
  disconnect.mockReset();
});

describe("useStationUpdates", () => {
  it("starts empty with no update time and the default threshold", () => {
    const { result } = renderHook(() => useStationUpdates());

    expect(result.current.stations).toEqual([]);
    expect(result.current.lastUpdatedAt).toBeNull();
    expect(result.current.atRiskThresholdMinutes).toBe(DEFAULT_AT_RISK_THRESHOLD_MINUTES);
    expect(connectToStationUpdates).toHaveBeenCalledTimes(1);
  });

  it("replaces the snapshot and stamps the receipt time on update", () => {
    const { result } = renderHook(() => useStationUpdates());
    const incoming = createMockStations(FIXED_NOW + 1);

    act(() => {
      handlers.onStations(overview(incoming));
    });

    expect(result.current.stations).toBe(incoming);
    expect(result.current.lastUpdatedAt).toBe(FIXED_NOW);
  });

  it("replaces only the threshold on a threshold event", () => {
    const { result } = renderHook(() => useStationUpdates());
    const incoming = createMockStations(FIXED_NOW + 1);
    act(() => {
      handlers.onStations(overview(incoming));
    });

    act(() => {
      handlers.onAtRiskThreshold({ atRiskThresholdMinutes: 25 });
    });

    expect(result.current.atRiskThresholdMinutes).toBe(25);
    expect(result.current.stations).toBe(incoming);
    expect(result.current.lastUpdatedAt).toBe(FIXED_NOW);
  });

  it("keeps the last snapshot and threshold on error after updates", () => {
    const { result } = renderHook(() => useStationUpdates());
    const received = createMockStations(FIXED_NOW + 1);
    act(() => {
      handlers.onStations(overview(received));
      handlers.onAtRiskThreshold({ atRiskThresholdMinutes: 30 });
    });

    act(() => {
      handlers.onError(new Error("SSE connection dropped"));
    });

    expect(result.current.stations).toBe(received);
    expect(result.current.lastUpdatedAt).toBe(FIXED_NOW);
    expect(result.current.atRiskThresholdMinutes).toBe(30);
  });

  it("keeps the empty snapshot and default threshold on error before any update arrives", () => {
    const { result } = renderHook(() => useStationUpdates());

    act(() => {
      handlers.onError(new Error("SSE connection dropped"));
    });

    expect(result.current.stations).toEqual([]);
    expect(result.current.lastUpdatedAt).toBeNull();
    expect(result.current.atRiskThresholdMinutes).toBe(DEFAULT_AT_RISK_THRESHOLD_MINUTES);
  });

  it("disconnects on unmount", () => {
    const { unmount } = renderHook(() => useStationUpdates());

    expect(disconnect).not.toHaveBeenCalled();
    unmount();

    expect(disconnect).toHaveBeenCalledTimes(1);
  });
});
