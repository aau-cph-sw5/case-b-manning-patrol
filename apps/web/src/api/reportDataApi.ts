/** Fetch historical compliance data through the authenticated API v2 client. */
import { authFetch } from '@/api/authFetch'
import type { ApiError, TrainsUpdate } from '@/api/dashboardApi'

/** Describe the subset of the API v2 `ReportData` response displayed in the report. */
export interface ReportData extends Pick<
  TrainsUpdate,
  'manning_percent' | 'm1m2_manning_percent' | 'm3m4_manning_percent'
> {
  /** Scheduled shift boundaries as ISO 8601 timestamps with offsets. */
  shift: { start: string; end: string }
  /** Evaluation cutoff as an ISO 8601 timestamp. It can precede the scheduled end. */
  as_of: string
}

const accessErrorMessages: Partial<Record<number, string>> = {
  401: 'Din adgang kunne ikke bekræftes (401).',
  403: 'Du har ikke adgang til rapporten (403).',
}

/** Prefer the local access message, then the API error body or HTTP status. */
async function toReportError(response: Response): Promise<Error> {
  const accessMessage = accessErrorMessages[response.status]
  if (accessMessage) return new Error(accessMessage)

  const error: ApiError | null = await response.json().catch(() => null)
  return new Error(error?.message ?? `Serveren svarede med HTTP ${response.status}.`)
}

/**
 * Fetch `GET /api/v2/report_data` using the API v2 `ReportData` response schema.
 *
 * Send the shift's Copenhagen start date as YYYY-MM-DD and omit `known_at`
 * so that late events and corrections can be included on each fetch.
 *
 * @throws Danish access errors for 401 and 403. Other HTTP failures use the
 * server message or status. Network and cancellation errors propagate.
 */
export async function getReportData(date: string, signal: AbortSignal): Promise<ReportData> {
  const query = new URLSearchParams({ date })
  const response = await authFetch(`/api/v2/report_data?${query}`, { signal, cache: 'no-store' })

  if (!response.ok) throw await toReportError(response)

  return response.json() as Promise<ReportData>
}
