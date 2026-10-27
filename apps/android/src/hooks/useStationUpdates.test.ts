// pins the contract of the station list hook: the snapshot starts empty, a
// receipt replaces it and stamps the update time, an error deliberately keeps
// the last snapshot, and unmount disconnects. happy-dom only for the hook
// renderer; the stream connection itself is a mock.
// @vitest-environment happy-dom
import { renderHook, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useStationUpdates } from "@/hooks/useStationUpdates";
import { createMockStations } from "@/fixtures/mockStations";
import type { Station, StationOverview } from "@/types/station";

const { connectToStationUpdates, disconnect } = vi.hoisted(() => ({
  connectToStationUpdates: vi.fn(),
  disconnect: vi.fn(),
}));

vi.mock("@/api/stationEventStream", () => ({
  connectToStationUpdates,
}));

const FIXED_NOW = 1760000000000;

let onUpdate: (data: StationOverview) => void;
let onError: (error: unknown) => void;

function overview(stations: Station[]): StationOverview {
  return { stations };
}

beforeEach(() => {
  vi.spyOn(Date, "now").mockReturnValue(FIXED_NOW);
  connectToStationUpdates.mockImplementation((on, err) => {
    onUpdate = on;
    onError = err;
    return disconnect;
  });
});

afterEach(() => {
  vi.restoreAllMocks();
  connectToStationUpdates.mockReset();
  disconnect.mockReset();
});

describe("useStationUpdates", () => {
  it("starts empty with no update time", () => {
    const { result } = renderHook(() => useStationUpdates());

    expect(result.current.stations).toEqual([]);
    expect(result.current.lastUpdatedAt).toBeNull();
    expect(connectToStationUpdates).toHaveBeenCalledTimes(1);
  });

  it("replaces the snapshot and stamps the receipt time on update", () => {
    const { result } = renderHook(() => useStationUpdates());
    const incoming = createMockStations(FIXED_NOW + 1);

    act(() => {
      onUpdate(overview(incoming));
    });

    expect(result.current.stations).toBe(incoming);
    expect(result.current.lastUpdatedAt).toBe(FIXED_NOW);
  });

  it("keeps the last snapshot on error after a successful update", () => {
    const { result } = renderHook(() => useStationUpdates());
    const received = createMockStations(FIXED_NOW + 1);
    act(() => {
      onUpdate(overview(received));
    });

    act(() => {
      onError(new Error("SSE connection dropped"));
    });

    expect(result.current.stations).toBe(received);
    expect(result.current.lastUpdatedAt).toBe(FIXED_NOW);
  });

  it("keeps the empty snapshot on error before any update arrives", () => {
    const { result } = renderHook(() => useStationUpdates());

    act(() => {
      onError(new Error("SSE connection dropped"));
    });

    expect(result.current.stations).toEqual([]);
    expect(result.current.lastUpdatedAt).toBeNull();
  });

  it("disconnects on unmount", () => {
    const { unmount } = renderHook(() => useStationUpdates());

    expect(disconnect).not.toHaveBeenCalled();
    unmount();

    expect(disconnect).toHaveBeenCalledTimes(1);
  });
});
