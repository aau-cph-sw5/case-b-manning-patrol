/**
 * Credentials for requests to the backend.
 *
 * There is no sign-in yet, so the "token" is the bare role claim read from
 * `EXPO_PUBLIC_ROLE`. It is inlined into the app bundle in plain text: it
 * tells the backend which role the client acts as, it does not prove it.
 * Replacing this with a real identity-provider token only changes this module;
 * callers already send whatever it returns as a bearer token.
 */

import { MOCK_ANDROID_ID } from "./mockBeacons";

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

/**
 * Return this device's android id, sent as the `X-Android-Id` header.
 *
 * Consensus: android_id == user, each phone is personal, so the backend binds
 * "own record" access to this id. Dev returns the mock id; a later real
 * implementation reads the device id (e.g. expo-application) here without
 * changing callers.
 */
export async function getAndroidId(): Promise<string> {
  return MOCK_ANDROID_ID;
}
