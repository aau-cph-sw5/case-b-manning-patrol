import { useState } from 'react'
import { STATIONS } from '../data/mockData.tsx'
import StationCard from './StationCard.tsx'
import {
  formatRemaining,
  remainingMinutes,
  timeColorClass,
} from '../utils/TimeColor.tsx'
import { useNow } from '../hooks/useNow.ts'
import { AttentionTime } from '../settings.ts'
import Legend from './Legend.tsx'

function Dashboard() {
  const now = useNow()
  const [attentionTime, setAttentionTime] = useState<number>(AttentionTime)

  const attention = STATIONS.flatMap((station) =>
    station.levels.map((level) => ({
      code: `${station.code}_${level.label}`,
      minutes: remainingMinutes(level, now),
    })),
  )
    .filter((item) => item.minutes <= attentionTime)
    .sort((a, b) => a.minutes - b.minutes)

const overdueCount = STATIONS.flatMap((station) => station.levels)
  .filter((level) => remainingMinutes(level, now) <= 0)
  .length

  return (
    <>
      <section className="dashboard-header">
        <Legend attentionTime={attentionTime} onAttentionTimeChange={setAttentionTime} />
        <h1 className='dashboard-title'>Manning Patrol Dashboard</h1>
      </section>
      <div className="dash">
        <div className={`overdue-count${overdueCount > 0 ? ' has-overdue' : ''}`} style={{ gridColumn: 2 }}>
          Overskredet ({overdueCount})
        </div>
        <section className="station-grid">
          {STATIONS.map((station) => (
            <StationCard key={station.code} station={station} now={now} attentionTime={attentionTime} />
          ))}
        </section>
        <aside className="card attention">
          <h2>ATTENTION ({attention.length})</h2>
          <ul className="attention-list">
            {attention.map((item) => (
              <li key={item.code} className={timeColorClass(item.minutes, attentionTime)}>
                {item.code}: {formatRemaining(item.minutes)}
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </>
  )
}

export default Dashboard
