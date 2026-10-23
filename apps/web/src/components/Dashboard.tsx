import { useRef } from 'react'
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
import { AttentionTime } from '../settings.ts'

import './Dashboard.css'

function Dashboard() {
  const now = useNow()
  const listRef = useRef<HTMLUListElement>(null)
  const fit = useFitCount(listRef)

  const attention = STATIONS.flatMap((station) =>
    station.levels.map((level) => ({
      code: `${station.code}_${level.label}`,
      minutes: remainingMinutes(level, now, station.code),
    })),
  )
    .filter((item) => item.minutes <= AttentionTime)
    .sort((a, b) => a.minutes - b.minutes)

  const visibleAttention =
    attention.length > fit ? attention.slice(0, fit - 1) : attention
  const hiddenCount = attention.length - visibleAttention.length

const overdueCount = STATIONS.flatMap((station) => station.levels)
  .filter((level) => remainingMinutes(level, now, station.code) <= 0)
  .length

  return (
    <>
      <section className="dashboard-header">
        <h1 className='dashboard-title'>Manning Patrol Dashboard</h1>
      <div className={`overdue-count${overdueCount > 0 ? ' has-overdue' : ''}`}>
        OVERDUE ({overdueCount})
      </div>
      </section>
      <div className="dash">
        <section className="station-grid">
          {STATIONS.map((station) => (
            <StationCard key={station.code} station={station} now={now} />
          ))}
        </section>
        <aside className="card attention">
          <h2>ATTENTION ({attention.length})</h2>
          <ul className="attention-list" ref={listRef}>
            {visibleAttention.map((item) => {
              const color = timeColorClass(item.minutes) as TimeColor
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
