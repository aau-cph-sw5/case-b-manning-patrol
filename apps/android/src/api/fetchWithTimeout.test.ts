// pins fetchWithTimeout: a response within the deadline passes through
// untouched, a request that never answers is aborted at the deadline, and a
// fetch that rejects on its own still rejects.
import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchWithTimeout } from "@/api/fetchWithTimeout";

const URL = "http://backend.test/api";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("fetchWithTimeout", () => {
  it("returns the response when fetch resolves within the deadline", async () => {
    const response = new Response("{}", { status: 200 });
    const fetchMock = vi.fn().mockResolvedValue(response);
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchWithTimeout(URL, { method: "POST" }, 1000)).resolves.toBe(response);
    expect(fetchMock).toHaveBeenCalledWith(URL, expect.objectContaining({ method: "POST" }));
  });

  it("sends the access token as a bearer Authorization header", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await fetchWithTimeout(URL);

    const headers = new Headers(fetchMock.mock.calls[0][1].headers);
    expect(headers.get("Authorization")).toBe("Bearer steward");
  });

  it("keeps the caller's own headers next to the Authorization header", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await fetchWithTimeout(URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    const headers = new Headers(fetchMock.mock.calls[0][1].headers);
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.get("Authorization")).toBe("Bearer steward");
  });

  it("aborts a request that never answers once the deadline passes", async () => {
    vi.useFakeTimers();
    // a fetch that only settles when its signal aborts, like a hung connection
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url: string, init?: RequestInit) =>
          new Promise<Response>((_resolve, reject) => {
            init?.signal?.addEventListener("abort", () =>
              reject(new DOMException("The operation was aborted.", "AbortError")),
            );
          }),
      ),
    );

    const promise = fetchWithTimeout(URL, undefined, 1000);
    const assertion = expect(promise).rejects.toMatchObject({ name: "AbortError" });
    await vi.advanceTimersByTimeAsync(1000);
    await assertion;
  });
});
