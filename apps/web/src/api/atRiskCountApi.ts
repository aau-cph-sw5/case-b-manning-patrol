/**
 * Fetches the at-risk episode count for the latest shift from the backend.
 * Uses the API v2 positioning interface and a relative URL proxied by Vite
 * to the backend.
 */
import { authFetch } from '@/api/authFetch'

const URL = '/api/v2/coverage/at-risk-count'

export interface AtRiskCount {
  shift_start: string
  episodes: number
}

export async function getAtRiskCount(): Promise<AtRiskCount> {
  const res = await authFetch(URL)
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.message ?? `Request failed: ${res.status}`)
  }
  return (await res.json()) as AtRiskCount
}