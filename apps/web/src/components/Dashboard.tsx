import { useEffect, useMemo, useState } from 'react'
import { BsEmojiFrown } from 'react-icons/bs'
import StationCard from './StationCard.tsx'
import TrainCard from './TrainCard.tsx'
import LineGroupFilter from './LineGroupFilter.tsx'
import { LINE_GROUPS, stationServesLineGroup, type LineGroup } from '../utils/lineGroup.ts'
import {
  formatRemaining,
  remainingMinutes,
  STATUS_ICONS,
  timeColorClass,
  type TimeColor,
} from '../utils/TimeColor.tsx'
import { useNow } from '../hooks/useNow.ts'
import { RiskTime, setRiskTime } from '../settings.ts'
import { getAtRiskThreshold, setAtRiskThreshold } from '../api/configApi.ts'
import { getAtRiskCount } from '../api/atRiskCountApi.ts'
import { toViewStations } from '../api/dashboardMapper.ts'
import { useDashboardStream } from '../hooks/useDashboardStream'
import { useTrainStream } from '../hooks/useTrainStream'
import Legend from './Legend.tsx'
import { formatTimestamp } from '../utils/FormatTimestamp.tsx'

import './Dashboard.css'

/** How often the at-risk episode count is refetched, in milliseconds. */
const AT_RISK_COUNT_POLL_MS = 30_000

function Dashboard() {
  const now = useNow()
  const [riskTime, setRiskTimeState] = useState<number>(RiskTime)
  const [lineGroup, setLineGroup] = useState<LineGroup>(LINE_GROUPS[0])
  const { dashboard, isLoading, error, lastUpdated } = useDashboardStream()
  const stations = useMemo(
    () => (dashboard ? toViewStations(dashboard) : []),
    [dashboard],
  )
  const { trainsUpdate } = useTrainStream()

  useEffect(() => {
    if (!import.meta.env.DEV) return
    if (dashboard) console.log('Dashboard SSE update:', dashboard)
    if (error) console.error('SSE error:', error)
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

  const [atRiskEpisodes, setAtRiskEpisodes] = useState<number | null>(0)

  useEffect(() => {
    const load = () =>
      getAtRiskCount()
        .then((count) => setAtRiskEpisodes(count.episodes))
        .catch((error) => {
          setAtRiskEpisodes(null)
          console.error('Error fetching at-risk count:', error)
        })
    load()
    const id = setInterval(load, AT_RISK_COUNT_POLL_MS)
    return () => clearInterval(id)
  }, [])

  const handleRiskTimeChange = (value: number) => {
    setRiskTime(value)
    setRiskTimeState(value)
    setAtRiskThreshold(value)
      .then((updated) => setRiskTimeState(updated.at_risk_threshold_minutes))
      .catch(console.error)
  }

  const attention = stations
    .filter((station) => stationServesLineGroup(station, lineGroup))
    .flatMap((station) =>
      station.levels.map((level) => ({
        code: `${station.stationId}_${level.label}`,
        minutes: remainingMinutes(level, now),
      })),
    )
    .filter((item) => item.minutes <= riskTime)
    .sort((a, b) => a.minutes - b.minutes)

  // the warn pill is about overdue stations only (not at-risk within the threshold)
  const overdueCount = attention.filter((item) => item.minutes <= 0).length

  const visibleStations = stations.filter((station) =>
    stationServesLineGroup(station, lineGroup),
  )

  return (
    <div className="dashboard-page">
      <header className="topbar">
        <div className="brand">
          <span className="logo">METRO</span>
          <span className="last-updated">Sidst opdateret: {formatTimestamp(lastUpdated)}</span>
        </div>
        <div className="topbar-right">
          <LineGroupFilter selected={lineGroup} onSelect={setLineGroup} />
        </div>
      </header>

      <div className="legend-row">
        <div className="nav-pill at-risk-total" role="status">
          I risiko denne vagt ({atRiskEpisodes ?? '-'})
        </div>
        {overdueCount > 0 && (
          <div className="nav-pill warn" role="status">
            <BsEmojiFrown className="smiley-icon" /> Overskredet stationer ({overdueCount})
          </div>
        )}
        <Legend riskTime={riskTime} onRiskTimeChange={handleRiskTimeChange} />
      </div>

      <main className="dash">
        <div className="side-col">
          <TrainCard update={trainsUpdate} lineGroup={lineGroup} />
          <aside className="card attention">
            <h2>Kræver handling ({attention.length})</h2>
            <ul className="attention-list">
              {attention.map((item) => {
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
            </ul>
          </aside>
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
          {visibleStations.map((station) => (
            <StationCard key={station.stationId} station={station} now={now} riskTime={riskTime} />
          ))}
        </section>
      </main>
    </div>
  )
}

export default Dashboard
