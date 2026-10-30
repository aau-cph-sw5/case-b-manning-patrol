/** Relative to the page; the Vite dev server proxies `/api` to localhost:8000. */
const URL = '/api/v2/config/at-risk-threshold'

/**
 * Fetch the at-risk threshold from the backend.
 *
 * @returns The threshold in minutes.
 * @throws Error if the response status is not 2xx. Network failures reject
 * with fetch's own error.
 */
export async function getAtRiskThreshold(): Promise<number> {
  const res = await fetch(URL)
  if (!res.ok) throw new Error(`GET failed: ${res.status}`)
  return (await res.json()).at_risk_threshold_minutes
}

/**
 * Store a new at-risk threshold on the backend with a POST.
 *
 * @param minutes - The new threshold in minutes.
 * @throws Error if the response status is not 2xx. Network failures reject
 * with fetch's own error.
 */
export async function setAtRiskThreshold(minutes: number): Promise<void> {
  const res = await fetch(URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ at_risk_threshold_minutes: minutes }),
  })
  if (!res.ok) throw new Error(`POST failed: ${res.status}`)
}