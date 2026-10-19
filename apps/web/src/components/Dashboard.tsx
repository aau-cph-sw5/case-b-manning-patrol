import { STATIONS } from '../data/mockData.tsx'
import StationCard from './StationCard.tsx'
import {
  formatRemaining,
  remainingMinutes,
  timeColorClass,
} from '../utils/TimeColor.tsx'
import { useNow } from '../hooks/useNow.ts'
import { AttentionTime } from '../settings.ts'

import './Dashboard.css'

function Dashboard() {
  const now = useNow()

  const attention = STATIONS.flatMap((station) =>
    station.levels.map((level) => ({
      code: `${station.code}_${level.label}`,
      minutes: remainingMinutes(level, now),
    })),
  )
    .filter((item) => item.minutes <= AttentionTime)
    .sort((a, b) => a.minutes - b.minutes)

const overdueCount = STATIONS.flatMap((station) => station.levels)
  .filter((level) => remainingMinutes(level, now) <= 0)
  .length

  return (
    <>
      <section className="dashboard-header">
        <h1 className='dashboard-title'>Manning Patrol Dashboard</h1>
      <div className={`overdue-count${overdueCount > 0 ? ' has-overdue' : ''}`}>
        Overdue: {overdueCount}
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
          <ul className="attention-list">
            {attention.map((item) => (
              <li key={item.code} className={timeColorClass(item.minutes)}>
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
