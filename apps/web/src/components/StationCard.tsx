import type { Station } from '../data/stationView'
import {
  formatRemaining,
  remainingMinutes,
  timeColorClass,
} from '../utils/TimeColor'

function StationCard({ station, now }: { station: Station; now: number }) {
  return (
    <article className="card station-card">
      <h2>{station.name}</h2>
      <ul className="levels">
        {station.levels.map((level) => {
          const minutes = remainingMinutes(level, now)
          return (
            <li key={level.label} className={timeColorClass(minutes)}>
              {level.label}: {formatRemaining(minutes)}
            </li>
          )
        })}
      </ul>
    </article>
  )
}

export default StationCard
