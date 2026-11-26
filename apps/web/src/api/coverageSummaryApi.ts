/**
 * Fetches the histogram of when overdue and at-risk episodes began during
 * one shift, from the backend, for the bar chart on the summary page.
 */
import { authFetch } from '@/api/authFetch'

const URL = '/api/v2/coverage/summary'

/** Episode counts for the hour of the shift the episodes began in. */
export interface DurationBucket {
  /** Hours-into-shift range label like "0:00-0:59". */
  label: string
  overdue_count: number
  at_risk_count: number
}

export interface CoverageSummary {
  shift_start: string
  buckets: DurationBucket[]
}

/** Return the onset histogram for the latest shift, or the given shift start. */
export async function getCoverageSummary(shiftStart?: string): Promise<CoverageSummary> {
  const url = shiftStart ? `${URL}?shift_start=${encodeURIComponent(shiftStart)}` : URL
  const res = await authFetch(url)
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.message ?? `Request failed: ${res.status}`)
  }
  return (await res.json()) as CoverageSummary
}
