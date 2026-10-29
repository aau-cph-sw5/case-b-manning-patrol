import { useEffect, useRef, useState } from 'react'
import { STATIONS } from '../data/mockData.tsx'
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
import { useDashboardStream } from '../hooks/useDashboardStream'
import Legend from './Legend.tsx'
import { formatTimestamp } from '../utils/FormatTimestamp.tsx'

import './Dashboard.css'

function Dashboard() {
  const now = useNow()
  const listRef = useRef<HTMLUListElement>(null)
  const fit = useFitCount(listRef)
  const [riskTime, setRiskTimeState] = useState<number>(RiskTime)
  const { dashboard, error, lastUpdated } = useDashboardStream()

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
    // Update the backend with the new risk time
    setAtRiskThreshold(value)
      .then((updated) => setRiskTimeState(updated.at_risk_threshold_minutes))
      .catch(console.error)
  }

  const attention = STATIONS.flatMap((station) =>
    station.levels.map((level) => ({
      code: `${station.code}_${level.label}`,
      minutes: remainingMinutes(level, now, station.code),
    })),
  )
    .filter((item) => item.minutes <= riskTime)
    .sort((a, b) => a.minutes - b.minutes)

  const visibleAttention =
    attention.length > fit ? attention.slice(0, fit - 1) : attention
  const hiddenCount = attention.length - visibleAttention.length

  const overdueCount = STATIONS.flatMap((station) =>
    station.levels.filter(
      (level) => remainingMinutes(level, now, station.code) <= 0,
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
          {STATIONS.map((station) => (
            <StationCard key={station.code} station={station} now={now} riskTime={riskTime} />
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
