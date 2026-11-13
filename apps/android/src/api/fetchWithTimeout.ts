/**
 * fetch() with a deadline and the client's credentials.
 *
 * A bare fetch to an unreachable host (stale backend IP, wrong Wi-Fi) can
 * hang for minutes waiting on TCP retransmits; a refused port fails fast, an
 * unreachable one does not. Callers that show a pending UI — the session
 * slider, the history loading state — would stay in it forever. Aborting
 * after a timeout turns the hang into an ordinary rejection, which callers
 * already handle as "backend unreachable".
 */
import { getAccessToken } from "@/api/auth";

/** How long a request may take before it counts as unreachable. */
const DEFAULT_TIMEOUT_MS = 10_000;

/**
 * Fetch a url, rejecting with an abort error when it takes longer than `timeoutMs`.
 *
 * Adds `Authorization: Bearer <token>` from {@link getAccessToken}; the
 * caller's own headers are kept, and the Authorization header always wins.
 *
 * @returns The response, exactly as fetch would return it; non-2xx still resolves.
 */
export async function fetchWithTimeout(
  url: string,
  init?: RequestInit,
  timeoutMs: number = DEFAULT_TIMEOUT_MS,
): Promise<Response> {
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${await getAccessToken()}`);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, headers, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}
