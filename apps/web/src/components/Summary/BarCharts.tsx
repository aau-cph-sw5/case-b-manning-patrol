import { useEffect, useState } from 'react'
import { BarChart } from '@mui/x-charts/BarChart'
import { getCoverageSummary, type DurationBucket } from '@/api/coverageSummaryApi'
import './BarCharts.css'

/** The shift length the x axis always spans, in hours. */
const AXIS_HOURS = 6

/**
 * Pad the fetched buckets with empty hours so the axis always spans
 * AXIS_HOURS even when the last event happened earlier.
 */
function paddedBuckets(buckets: DurationBucket[]): DurationBucket[] {
  const padded: DurationBucket[] = []
  for (let hour = 0; hour < AXIS_HOURS; hour++) {
    padded.push(
      buckets[hour] ?? {
        label: `${hour}:00-${hour}:59`,
        overdue_count: 0,
        at_risk_count: 0,
      },
    )
  }
  return padded
}

/**
 * Histogram of when stations went overdue or at-risk during the latest
 * shift, per one-hour bucket, fetched on mount from
 * GET /api/v2/coverage/summary. Shows an error message when the request fails.
 */
export default function BarCharts() {
  const [buckets, setBuckets] = useState<DurationBucket[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getCoverageSummary()
      .then((summary) => setBuckets(paddedBuckets(summary.buckets)))
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div className="bar-charts">
      <section className="card bar-chart-card">
        <h2>Overskredet station bemandelse</h2>
        {error && <p className="bar-charts-error">Kunne ikke hente data: {error}</p>}
        <BarChart
          series={[
            {
              type: 'bar',
              data: buckets.map((b) => b.overdue_count),
              label: 'Overskredet',
            },
            {
              type: 'bar',
              data: buckets.map((b) => b.at_risk_count),
              label: 'I risiko',
            },
          ]}
          xAxis={[{ scaleType: 'band', data: buckets.map((b) => b.label) }]}
        />
      </section>
    </div>
  )
}
