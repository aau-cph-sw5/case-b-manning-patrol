/** Card listing one station's levels with their countdowns. */
import type { Station } from '../api/dashboardMapper'

import {
  formatRemaining,
  remainingMinutes,
  STATUS_ICONS,
  timeColorClass,
  type TimeColor,
} from '../utils/TimeColor'
import { ROUTE_COLORS } from '../utils/lineGroup'

import './StationCard.css'

/**
 * Render one station's levels, each with a colour, a face icon and the time
 * left.
 *
 * `now` is the current time in epoch ms and `riskTime` the at-risk threshold
 * in minutes; levels with that many minutes or fewer left turn yellow.
 */
function StationCard({ station, now, riskTime }: { station: Station; now: number; riskTime: number }) {
  const rows = station.levels.map((level) => ({
    level,
    minutes: remainingMinutes(level, now),
  }))
  const worst = rows.reduce((min, row) => Math.min(min, row.minutes), 60)
  const worstColor = timeColorClass(worst, riskTime) as TimeColor
  const WorstIcon = STATUS_ICONS[worstColor]

  return (
    <article className="card station-card">
      <header className="station-card-head">
        <div className="station-title">
          {station.lines.length > 0 && (
            <div className="route-badges">
              {station.lines.map((line) => (
                <span
                  key={line}
                  className="route-badge"
                  style={{
                    backgroundColor: ROUTE_COLORS[line] ?? '#686868',
                    color: line === 'M2' ? '#000000' : '#ffffff',
                  }}
                >
                  {line}
                </span>
              ))}
            </div>
          )}
          <h2>{station.name}</h2>
        </div>
        <WorstIcon className={`smiley-icon station-status ${worstColor.replace('row-', 'text-')}`} />
      </header>
      <ul className="levels">
        {rows.map(({ level, minutes }) => {
          const color = timeColorClass(minutes, riskTime) as TimeColor
          const StatusIcon = STATUS_ICONS[color]
          return (
            <li key={level.label} className={color}>
              <StatusIcon className="smiley-icon" />
              <span>{level.label}: {formatRemaining(minutes)}</span>
            </li>
          )
        })}
      </ul>
    </article>
  )
}

export default StationCard
