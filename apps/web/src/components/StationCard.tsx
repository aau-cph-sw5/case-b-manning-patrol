import type { Station } from '../data/mockData'
import { timeColorClass, type TimeColor } from '../utils/TimeColor'
import { BsEmojiFrown, BsEmojiNeutral, BsEmojiSmile } from 'react-icons/bs';
import type { IconType } from 'react-icons'

const STATUS_ICONS: Record<TimeColor, IconType> = {
  'row-green': BsEmojiSmile,
  'row-yellow': BsEmojiNeutral,
  'row-red': BsEmojiFrown,
}

function StationCard({ station }: { station: Station }) {
  return (
    <article className="card station-card">
      <h2>{station.name}</h2>
      <ul className="levels">
        {station.levels.map((level) => {
          const color = timeColorClass(level.value)
          const StatusIcon = STATUS_ICONS[color]
          return (
            <li key={level.label} className={color}>
              <StatusIcon className='smiley-icon'/> {level.label}: {level.value}
            </li>
          )
        })}
      </ul>
    </article>
  )
}

export default StationCard