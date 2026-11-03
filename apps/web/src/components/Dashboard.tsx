/** The control room dashboard page. */
import { useEffect, useMemo, useRef, useState } from 'react'
import StationCard from './StationCard.tsx'
import {
  formatRemaining,
  remainingMinutes,
  STATUS_ICONS,
  timeColorClass,
  type TimeColor,
} from '../utils/TimeColor.tsx'
import { useNow } from '../hooks/useNow.ts'
import { useFitCount } from '../hooks/useFitCount.ts'
import { RiskTime, setRiskTime } from '../settings.ts'
import { getAtRiskThreshold, setAtRiskThreshold } from '../api/configApi.ts'
import { toViewStations } from '../api/dashboardMapper.ts'
import { useDashboardStream } from '../hooks/useDashboardStream'
import Legend from './Legend.tsx'
import { formatTimestamp } from '../utils/FormatTimestamp.tsx'

import './Dashboard.css'

/**
 * Render the control room dashboard: a card per station, the number of
 * overdue levels, and a list of levels at risk or overdue, most urgent first.
 *
 * Stations come from {@link useDashboardStream}, and every update and error
 * from it is logged to the console. Countdowns re-render every second through
 * {@link useNow}. The at-risk threshold is fetched from the backend once on
 * mount. Editing it in the legend applies the new value at once and then posts
 * it, adopting the value the backend returns; if either request fails, the
 * error is only logged and the local value stays.
 *
 * The attention list shows as many rows as fit (see {@link useFitCount}); when
 * rows are cut, the last visible row becomes a "+N" counter instead.
 */
function Dashboard() {
  const now = useNow()
  const listRef = useRef<HTMLUListElement>(null)
  const fit = useFitCount(listRef)
  const [riskTime, setRiskTimeState] = useState<number>(RiskTime)
  const { dashboard, isLoading, error, lastUpdated } = useDashboardStream()
  const stations = useMemo(
    () => (dashboard ? toViewStations(dashboard) : []),
    [dashboard],
  )

  useEffect(() => {
    if (dashboard) console.log("Dashboard SSE update:", dashboard);
    if (error) console.error("SSE error:", error);
  }, [dashboard, error])

  useEffect(() => {
    getAtRiskThreshold()
      .then((threshold) => {
        setRiskTime(threshold.at_risk_threshold_minutes)
        setRiskTimeState(threshold.at_risk_threshold_minutes)
      })
      .catch((error) => {
        console.error('Error fetching at-risk threshold:', error)
      })
  }, [])

  const handleRiskTimeChange = (value: number) => {
    setRiskTime(value)
    setRiskTimeState(value)
    setAtRiskThreshold(value)
      .then((updated) => setRiskTimeState(updated.at_risk_threshold_minutes))
      .catch(console.error)
  }

  const attention = stations.flatMap((station) =>
    station.levels.map((level) => ({
      code: `${station.stationId}_${level.label}`,
      minutes: remainingMinutes(level, now),
    })),
  )
    .filter((item) => item.minutes <= riskTime)
    .sort((a, b) => a.minutes - b.minutes)

  const visibleAttention =
    attention.length > fit ? attention.slice(0, fit - 1) : attention
  const hiddenCount = attention.length - visibleAttention.length

  const overdueCount = stations.flatMap((station) =>
    station.levels.filter(
      (level) => remainingMinutes(level, now) <= 0,
    ),
  ).length

  return (
    <>
      <section className="dashboard-header">
        <Legend riskTime={riskTime} onRiskTimeChange={handleRiskTimeChange} />
        <h1 className='dashboard-title'>Patrulje Overblik</h1>
        <div className="last-updated">Sidst opdateret: {formatTimestamp(lastUpdated)}</div>
      </section>
      <div className="dash">
        <div className={`overdue-count${overdueCount > 0 ? ' has-overdue' : ''}`} style={{ gridColumn: 2, marginTop: "10px" }}>
          Overskredet ({overdueCount})
        </div>
        <section className="station-grid">
          {stations.length === 0 && (
            <p className="dashboard-empty">
              {error
                ? `Kunne ikke hente data: ${error.message}`
                : isLoading
                  ? 'Henter data…'
                  : 'Ingen stationer'}
            </p>
          )}
          {stations.map((station) => (
            <StationCard key={station.stationId} station={station} now={now} riskTime={riskTime} />
          ))}
        </section>
        <aside className="card attention">
          <h2>Kræver handling ({attention.length})</h2>
          <ul className="attention-list" ref={listRef}>
            {visibleAttention.map((item) => {
              const color = timeColorClass(item.minutes, riskTime) as TimeColor
              const StatusIcon = STATUS_ICONS[color]
              return (
                <li key={item.code} className={color}>
                  <StatusIcon className="smiley-icon" />
                  <span className="attention-text">
                    {item.code}: {formatRemaining(item.minutes)}
                  </span>
                </li>
              )
            })}
            {hiddenCount > 0 && (
              <li className="attention-more">+{hiddenCount}</li>
            )}
          </ul>
        </aside>
      </div>
    </>
  )
}

export default Dashboard
