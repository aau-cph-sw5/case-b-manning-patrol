/** Card listing one station's levels with their countdowns. */
import type { Station } from '../api/dashboardMapper'
import {
  formatRemaining,
  remainingMinutes,
  STATUS_ICONS,
  timeColorClass,
  type TimeColor,
} from '../utils/TimeColor'

/**
 * Render one station's levels, each with a colour, a face icon and the time
 * left.
 *
 * `now` is the current time in epoch ms and `riskTime` the at-risk threshold
 * in minutes; levels with that many minutes or fewer left turn yellow.
 */
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
