import { useStations } from '../hooks/useStations.ts'
import StationCard from './StationCard.tsx'
import {
  formatRemaining,
  remainingMinutes,
  timeColorClass,
} from '../utils/TimeColor.tsx'
import { useNow } from '../hooks/useNow.ts'

// areas with this many minutes or less left are listed under ATTENTION
const ATTENTION_THRESHOLD_MIN = 10

function Dashboard() {
  const now = useNow()
  const { stations, loading, error } = useStations()

  const attention = stations
    .flatMap((station) =>
      station.levels.map((level) => ({
        code: `${station.code}_${level.label}`,
        minutes: remainingMinutes(level, now),
      })),
    )
    .filter((item) => item.minutes <= ATTENTION_THRESHOLD_MIN)
    .sort((a, b) => a.minutes - b.minutes)

  if (loading) {
    return <p>Henter stationer...</p>
  }

  if (error) {
    return <p>{error}</p>
  }

  return (
    <>
      <h1>Manning Patrol Dashboard</h1>
      <div className="dash">
        <section className="station-grid">
          {stations.map((station) => (
            <StationCard key={station.code} station={station} now={now} />
          ))}
        </section>
        <aside className="card attention">
          <h2>ATTENTION ({attention.length})</h2>
          <ul className="attention-list">
            {attention.map((item) => (
              <li key={item.code} className={timeColorClass(item.minutes)}>
                {item.code} {formatRemaining(item.minutes)}
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </>
  )
}

export default Dashboard
