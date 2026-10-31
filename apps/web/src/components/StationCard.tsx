import type { Station } from '../api/dashboardMapper'
import {
  formatRemaining,
  remainingMinutes,
  STATUS_ICONS,
  timeColorClass,
  type TimeColor,
} from '../utils/TimeColor'

function StationCard({ station, now, riskTime }: { station: Station; now: number; riskTime: number }) {
  return (
    <article className="card station-card">
      <h2>{station.name}</h2>
      <ul className="levels">
        {station.levels.map((level) => {
          const minutes = remainingMinutes(level, now)
          const color = timeColorClass(minutes, riskTime) as TimeColor
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
