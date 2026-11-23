/**
 * Credentials for requests to the backend.
 *
 * There is no sign-in yet, so the "token" is the bare role claim read from
 * `VITE_ROLE`. Vite inlines it into the bundle in plain text: it tells the
 * backend which role the client acts as, it does not prove it. Replacing this
 * with a real identity-provider token only changes this module; callers send
 * whatever it returns as a bearer token.
 */

/** Role the dashboard acts as when `VITE_ROLE` is unset. */
const DEFAULT_ROLE = "controlRoomOperator";

/**
 * Return the bearer token to send with backend requests.
 *
 * Async so a later identity-provider implementation can fetch or refresh a
 * token without changing callers.
 */
export async function getAccessToken(): Promise<string> {
  return import.meta.env.VITE_ROLE ?? DEFAULT_ROLE;
}
