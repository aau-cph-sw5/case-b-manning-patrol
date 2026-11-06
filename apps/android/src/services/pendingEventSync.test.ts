// pins the pending event retry: after connectivity returns, every pending is
// re-POSTed with its original device timestamp — connect for open pendings,
// disconnect for closed ones — and only the accepted ones are counted.
import { afterEach, describe, expect, it, vi } from "vitest";

import { postConnectionEvent } from "@/api/postConnectionEvent";
import {
  addPendingRecord,
  clearPendingRecords,
  markPendingClosed,
} from "@/state/pendingRecords";
import { retryPendingConnectionEvents } from "@/services/pendingEventSync";

vi.mock("@/api/postConnectionEvent", () => ({
  postConnectionEvent: vi.fn().mockResolvedValue(undefined),
}));

const postMock = vi.mocked(postConnectionEvent);

const BEACON_A = "550e8400-e29b-41d4-a716-00000000000a";
const BEACON_B = "550e8400-e29b-41d4-a716-00000000000b";
const START_A = new Date("2025-10-09T10:00:00.000Z");
const END_A = new Date("2025-10-09T10:05:00.000Z");
const START_B = new Date("2025-10-09T11:00:00.000Z");

afterEach(() => {
  clearPendingRecords();
  postMock.mockClear();
});

describe("retryPendingConnectionEvents", () => {
  it("re-POSTs an open pending as CONNECTED with the original start timestamp", async () => {
    addPendingRecord(BEACON_A, START_A);

    await expect(retryPendingConnectionEvents()).resolves.toBe(1);
    expect(postMock).toHaveBeenCalledWith({
      event: "CONNECTED",
      beacon_id: BEACON_A,
      timestamp: START_A.toISOString(),
    });
  });

  it("re-POSTs a closed pending as CONNECTED then DISCONNECTED, both with original timestamps", async () => {
    addPendingRecord(BEACON_A, START_A);
    markPendingClosed(BEACON_A, END_A);

    // the backend pairs a disconnect with a stored connect, so both must be sent
    await expect(retryPendingConnectionEvents()).resolves.toBe(2);
    expect(postMock).toHaveBeenNthCalledWith(1, {
      event: "CONNECTED",
      beacon_id: BEACON_A,
      timestamp: START_A.toISOString(),
    });
    expect(postMock).toHaveBeenNthCalledWith(2, {
      event: "DISCONNECTED",
      beacon_id: BEACON_A,
      timestamp: END_A.toISOString(),
    });
  });

  it("counts only the events the backend accepted and keeps the rest pending", async () => {
    addPendingRecord(BEACON_A, START_A);
    markPendingClosed(BEACON_A, END_A); // would send 2 events
    addPendingRecord(BEACON_B, START_B); // 1 event
    postMock.mockRejectedValueOnce(new Error("still offline")); // A's connect fails, its disconnect is skipped

    await expect(retryPendingConnectionEvents()).resolves.toBe(1);
    expect(postMock).toHaveBeenCalledTimes(2);
  });

  it("does nothing when there are no pendings", async () => {
    await expect(retryPendingConnectionEvents()).resolves.toBe(0);
    expect(postMock).not.toHaveBeenCalled();
  });
});
