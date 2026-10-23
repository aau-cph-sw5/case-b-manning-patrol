import type { Station } from '../data/mockData'
import { BsEmojiFrown, BsEmojiNeutral, BsEmojiSmile } from 'react-icons/bs';
import type { IconType } from 'react-icons'
import {
  formatRemaining,
  remainingMinutes,
  timeColorClass,
  type TimeColor,
} from '../utils/TimeColor'

const STATUS_ICONS: Record<TimeColor, IconType> = {
  'row-green': BsEmojiSmile,
  'row-yellow': BsEmojiNeutral,
  'row-red': BsEmojiFrown,
}


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
