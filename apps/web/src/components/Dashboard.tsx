import { useState } from 'react'
import { STATIONS } from '../data/mockData.tsx'
import StationCard from './StationCard.tsx'
import {
  formatRemaining,
  remainingMinutes,
  timeColorClass,
} from '../utils/TimeColor.tsx'
import { useNow } from '../hooks/useNow.ts'
import { RiskTime, setRiskTime } from '../settings.ts'
import Legend from './Legend.tsx'

function Dashboard() {
  const now = useNow()
  const [riskTime, setRiskTimeState] = useState<number>(RiskTime)
  const handleRiskTimeChange = (value: number) => {
    setRiskTime(value)
    setRiskTimeState(value)
  }

  const attention = STATIONS.flatMap((station) =>
    station.levels.map((level) => ({
      code: `${station.code}_${level.label}`,
      minutes: remainingMinutes(level, now),
    })),
  )
    .filter((item) => item.minutes <= riskTime)
    .sort((a, b) => a.minutes - b.minutes)

const overdueCount = STATIONS.flatMap((station) => station.levels)
  .filter((level) => remainingMinutes(level, now) <= 0)
  .length

  return (
    <>
      <section className="dashboard-header">
        <Legend riskTime={riskTime} onRiskTimeChange={handleRiskTimeChange} />
        <h1 className='dashboard-title'>Patrulje Overblik</h1>
      </section>
      <div className="dash">
        <div className={`overdue-count${overdueCount > 0 ? ' has-overdue' : ''}`} style={{ gridColumn: 2 }}>
          Overskredet ({overdueCount})
        </div>
        <section className="station-grid">
          {STATIONS.map((station) => (
            <StationCard key={station.code} station={station} now={now} riskTime={riskTime} />
          ))}
        </section>
        <aside className="card attention">
          <h2>Kræver handling ({attention.length})</h2>
          <ul className="attention-list">
            {attention.map((item) => (
              <li key={item.code} className={timeColorClass(item.minutes, riskTime)}>
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
