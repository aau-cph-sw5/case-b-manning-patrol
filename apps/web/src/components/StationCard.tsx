import type { Station } from '../data/mockData'
import {
  formatRemaining,
  remainingMinutes,
  STATUS_ICONS,
  timeColorClass,
  type TimeColor,
} from '../utils/TimeColor'

function StationCard({ station, now }: { station: Station; now: number }) {
  return (
    <article className="card station-card">
      <h2>{station.name}</h2>
      <ul className="levels">
        {station.levels.map((level) => {
          const minutes = remainingMinutes(level, now, station.code)
          const color = timeColorClass(minutes) as TimeColor
          const StatusIcon = STATUS_ICONS[color]
          return (
            <li key={level.label} className={color}>
              <StatusIcon className='smiley-icon'/> {level.label}: {formatRemaining(minutes)}
            </li>
          )
        })}
      </ul>
    </article>
  )
}

export default StationCard
