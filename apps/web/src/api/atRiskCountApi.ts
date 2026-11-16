import { authFetch } from '@/api/authFetch'

const URL = '/api/v2/coverage/at-risk-count'

export interface AtRiskCount {
  /** ISO 8601 start of the shift the episodes were counted for. */
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
