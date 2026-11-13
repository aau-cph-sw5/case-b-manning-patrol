/**
 * REST client for the at-risk threshold, GET and POST
 * `/api/v2/config/at-risk-threshold` (contracts/api/v2/positioning-interface).
 *
 * Uses a relative URL, so it relies on the Vite dev server proxying `/api` to
 * the backend; unlike the dashboard stream it ignores `VITE_API_URL`.
 */
import { authFetch } from '@/api/authFetch'

const URL = '/api/v2/config/at-risk-threshold'

/** The contract's AtRiskThreshold schema. */
export interface AtRiskThreshold {
  /** An area is at risk when this many minutes or fewer remain until it is overdue. At least 1. */
  at_risk_threshold_minutes: number
}

/**
 * Build an Error from a failed response, with the message of the contract's
 * Error schema (`{ code, message }`) when the body has one, otherwise the HTTP
 * status.
 */
async function toError(res: Response): Promise<Error> {
  try {
    const body = await res.json()
    return new Error(body.message ?? `Request failed: ${res.status}`)
  } catch {
    return new Error(`Request failed: ${res.status}`)
  }
}

/**
 * Fetch the current at-risk threshold from the backend.
 *
 * @throws Error with the backend's message on a non-2xx response; a network
 *   failure rejects with fetch's own error.
 */
export async function getAtRiskThreshold(): Promise<AtRiskThreshold> {
  const res = await authFetch(URL)
  if (!res.ok) throw await toError(res)
  return (await res.json()) as AtRiskThreshold
}

/**
 * Store a new at-risk threshold on the backend and return the stored value.
 *
 * The backend answers 400 for a value below 1.
 *
 * @throws Error with the backend's message on a non-2xx response; a network
 *   failure rejects with fetch's own error.
 */
export async function setAtRiskThreshold(minutes: number): Promise<AtRiskThreshold> {
  const res = await authFetch(URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ at_risk_threshold_minutes: minutes }),
  })
  if (!res.ok) throw await toError(res)
  return (await res.json()) as AtRiskThreshold
}