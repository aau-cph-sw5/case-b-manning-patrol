// pins the contract of the patrol history hook: it fetches on mount, exposes
// the server time, keeps the last good list when a fetch fails, and refetch()
// is a no-op while a request is in flight. happy-dom only for the hook
// renderer; the api call itself is a mock.
// @vitest-environment happy-dom
import { renderHook, act } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { usePatrolRecords } from "@/hooks/usePatrolRecords";
import { clearPendingRecords } from "@/state/pendingRecords";
import { notifyRecordsChanged, resetRecordsVersion } from "@/state/recordRefresh";
import type { Record, RecordList } from "@/types/patrol_records/record";

const { getPatrolRecords, retryMock } = vi.hoisted(() => ({
  getPatrolRecords: vi.fn(),
  retryMock: vi.fn().mockResolvedValue(0),
}));

vi.mock("@/api/getPatrolRecords", () => ({
  getPatrolRecords,
}));

vi.mock("@/services/pendingEventSync", () => ({
  retryPendingConnectionEvents: retryMock,
}));

function record(overrides: Partial<Record> = {}): Record {
  return {
    androidId: "660e8400-e29b-41d4-a716-446655440001",
    beaconId: "550e8400-e29b-41d4-a716-000000000002",
    startedAt: new Date("2025-10-09T10:00:00.000Z"),
    endedAt: null,
    durationSecs: null,
    minPatrolDurationSecs: 10,
    patrolled: false,
    status: "open",
    area: {
      areaId: "area-1",
      name: "Frederiksberg platform",
      line: ["M1"],
      stationId: "station-1",
      areaType: "platform",
    },
    ...overrides,
  };
}

function recordList(
  records: Record[],
  time = new Date("2025-10-09T12:00:00.000Z"),
): RecordList {
  return { records, time };
}

// flushes the microtask queue so the hook's promise callbacks have run
async function flush() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

afterEach(() => {
  getPatrolRecords.mockReset();
  retryMock.mockReset().mockResolvedValue(0);
  clearPendingRecords();
  resetRecordsVersion();
  vi.restoreAllMocks();
});

describe("usePatrolRecords", () => {
  it("fetches on mount and exposes the records with the server time", async () => {
    const list = recordList([record()]);
    getPatrolRecords.mockResolvedValue(list);

    const { result } = renderHook(() => usePatrolRecords());

    expect(result.current.loading).toBe(true);
    expect(result.current.records).toEqual([]);
    expect(result.current.serverTime).toBeNull();

    await flush();

    expect(getPatrolRecords).toHaveBeenCalledTimes(1);
    expect(result.current.records).toEqual(list.records);
    expect(result.current.serverTime).toBe(list.time);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("shows the steward-facing error when the mount fetch fails", async () => {
    getPatrolRecords.mockRejectedValue(new Error("network down"));

    const { result } = renderHook(() => usePatrolRecords());
    await flush();

    expect(result.current.error).toBe("Kunne ikke hente historikken. Prøv igen.");
    expect(result.current.loading).toBe(false);
    expect(result.current.records).toEqual([]);
  });

  it("keeps the last good list when a refetch fails", async () => {
    const list = recordList([record()]);
    getPatrolRecords.mockResolvedValueOnce(list).mockRejectedValueOnce(new Error("dropped"));

    const { result } = renderHook(() => usePatrolRecords());
    await flush();
    expect(result.current.records).toEqual(list.records);

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.records).toEqual(list.records);
    expect(result.current.error).toBe("Kunne ikke hente historikken. Prøv igen.");
    expect(result.current.loading).toBe(false);
  });

  it("replaces the records on a successful refetch and clears the error", async () => {
    const first = recordList([record()]);
    const second = recordList([
      record({ status: "closed", endedAt: new Date("2025-10-09T10:05:00.000Z"), durationSecs: 300, patrolled: true }),
    ]);
    getPatrolRecords.mockResolvedValueOnce(first).mockResolvedValueOnce(second);

    const { result } = renderHook(() => usePatrolRecords());
    await flush();

    await act(async () => {
      await result.current.refetch();
    });

    expect(getPatrolRecords).toHaveBeenCalledTimes(2);
    expect(result.current.records).toEqual(second.records);
    expect(result.current.serverTime).toBe(second.time);
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it("re-sends pending events after a successful fetch and reconciles with a second fetch", async () => {
    const first = recordList([record()]);
    const second = recordList([
      record({ status: "closed", endedAt: new Date("2025-10-09T10:05:00.000Z"), durationSecs: 300, patrolled: true }),
    ]);
    getPatrolRecords.mockResolvedValueOnce(first).mockResolvedValueOnce(second);
    retryMock.mockResolvedValue(1);

    const { result } = renderHook(() => usePatrolRecords());
    await flush();

    expect(retryMock).toHaveBeenCalledTimes(1);
    expect(getPatrolRecords).toHaveBeenCalledTimes(2);
    expect(result.current.records).toEqual(second.records);
    expect(result.current.serverTime).toBe(second.time);
  });

  it("refetches when an ingestion POST is acknowledged (records version bump)", async () => {
    getPatrolRecords.mockResolvedValue(recordList([record()]));

    const { result, rerender } = renderHook(() => usePatrolRecords());
    await flush();
    expect(getPatrolRecords).toHaveBeenCalledTimes(1);

    // a confirmed connect/disconnect was acked by the backend
    act(() => notifyRecordsChanged());
    rerender();
    await flush();

    expect(getPatrolRecords).toHaveBeenCalledTimes(2);
    expect(result.current.loading).toBe(false);
  });

  it("ignores refetch while a request is still in flight", async () => {
    let resolveFetch: (list: RecordList) => void = () => {};
    getPatrolRecords.mockImplementation(
      () =>
        new Promise<RecordList>((resolve) => {
          resolveFetch = resolve;
        }),
    );

    const { result } = renderHook(() => usePatrolRecords());

    await act(async () => {
      const mountFetch = result.current.refetch();
      await result.current.refetch();
      resolveFetch(recordList([record()]));
      await mountFetch;
    });

    expect(getPatrolRecords).toHaveBeenCalledTimes(1);
    expect(result.current.records).toHaveLength(1);
    expect(result.current.loading).toBe(false);
  });
});
