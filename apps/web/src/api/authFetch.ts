/**
 * fetch() with the client's credentials, for every REST call to the backend.
 */
import { getAccessToken } from "@/api/auth";

/**
 * Fetch a url with `Authorization: Bearer <token>` from {@link getAccessToken}.
 *
 * The caller's own headers are kept; the Authorization header always wins.
 *
 * @returns The response, exactly as fetch would return it; non-2xx still resolves.
 */
export async function authFetch(url: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${await getAccessToken()}`);
  return fetch(url, { ...init, headers });
}
