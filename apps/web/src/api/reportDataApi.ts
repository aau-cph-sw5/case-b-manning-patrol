/** Fetch historical compliance data through the authenticated API v2 client. */
import { authFetch } from '@/api/authFetch'
import type { ApiError, TrainsUpdate } from '@/api/dashboardApi'

/** Describe one train's staffing over the reported shift. */
export interface ReportTrain {
  /** Stable train UUID. */
  train_id: string
  /** Human-readable identifier for the train. */
  slug: string
  /** Metro lines the train serves. */
  line: string[]
  /** Share of running time staffed, from 0 to 1, or null when there was no running time. */
  manned_ratio: number | null
  /** Seconds staffed during the reported period. */
  manned_time: number
  /** Seconds in service during the reported period. */
  running_time: number
}

/** Describe the station and area fields displayed from the API v2 report. */
export interface ReportStation {
  station_id: string
  name: string
  areas: {
    area_id: string
    name: string
    /** Evaluated coverage at the report's `as_of` timestamp. */
    coverage_status: 'compliant' | 'overdue'
  }[]
}

/** Describe the subset of the Report API v2.9.0 response displayed on the report page. */
export interface ReportData extends Pick<
  TrainsUpdate,
  'manning_percent' | 'm1m2_manning_percent' | 'm3m4_manning_percent'
> {
  /** Scheduled shift boundaries as ISO 8601 timestamps with offsets. */
  shift: { start: string; end: string }
  /** Evaluation cutoff as an ISO 8601 timestamp. It can precede the scheduled end. */
  as_of: string
  stations: ReportStation[]
  trains: ReportTrain[]
}

/**
 * Fetch `GET /api/v2/report_data` using the API v2 `ReportData` response schema.
 *
 * Send the shift's Copenhagen start date as YYYY-MM-DD and omit `known_at`
 * so that late events and corrections can be included on each fetch.
 *
 * @throws Danish messages for 400, 401 and 403. Other HTTP failures use the
 * server message or status. Network and cancellation errors propagate.
 */
export async function getReportData(date: string, signal: AbortSignal): Promise<ReportData> {
  const query = new URLSearchParams({ date })
  const response = await authFetch(`/api/v2/report_data?${query}`, { signal, cache: 'no-store' })

  if (response.status === 400) {
    throw new Error('Vagten på den valgte dato er endnu ikke startet (400).')
  }
  if (response.status === 401) {
    throw new Error('Din adgang kunne ikke bekræftes (401).')
  }
  if (response.status === 403) {
    throw new Error('Du har ikke adgang til rapporten (403).')
  }
  if (!response.ok) {
    const error: ApiError | null = await response.json().catch(() => null)
    throw new Error(error?.message ?? `Serveren svarede med HTTP ${response.status}.`)
  }

  return response.json() as Promise<ReportData>
}
