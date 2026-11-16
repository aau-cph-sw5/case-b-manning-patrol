/**
 * Credentials for requests to the backend.
 *
 * There is no sign-in yet, so the "token" is the bare role claim read from
 * `EXPO_PUBLIC_ROLE`. It is inlined into the app bundle in plain text: it
 * tells the backend which role the client acts as, it does not prove it.
 * Replacing this with a real identity-provider token only changes this module;
 * callers already send whatever it returns as a bearer token.
 */

/** Role the steward app acts as when `EXPO_PUBLIC_ROLE` is unset. */
const DEFAULT_ROLE = "steward";

/**
 * Return the bearer token to send with backend requests.
 *
 * Async so a later identity-provider implementation can fetch or refresh a
 * token without changing callers.
 */
export async function getAccessToken(): Promise<string> {
  return process.env.EXPO_PUBLIC_ROLE ?? DEFAULT_ROLE;
}
