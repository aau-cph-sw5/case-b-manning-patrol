/**
 * Provide the configured dashboard role and API credentials.
 *
 * There is no sign-in yet, so the "token" is the bare role claim read from
 * `VITE_ROLE`. Vite inlines it into the bundle in plain text: it tells the
 * backend which role the client acts as. Callers use this module to obtain
 * credentials or decide which controls to display.
 */

const DEFAULT_ROLE = "controlRoomOperator";

function getRole(): string {
  return import.meta.env.VITE_ROLE ?? DEFAULT_ROLE;
}

/**
 * Return whether the configured role should see historical report controls.
 *
 * Operations Administrator can see the controls. The backend enforces
 * `historical_data` on each report request.
 */
export function canViewHistoricalData(): boolean {
  return getRole().trim() === "operations_administrator";
}

/**
 * Return the bearer token to send with backend requests.
 *
 * Async so a later identity-provider implementation can fetch or refresh a
 * token without changing callers.
 */
export async function getAccessToken(): Promise<string> {
  return getRole();
}
