import type { Station } from '../data/mockData'
import { timeColorClass } from '../utils/TimeColor'

function StationCard({ station }: { station: Station }) {
  return (
    <article className="card station-card">
      <h2>{station.name}</h2>
      <ul className="levels">
        {station.levels.map((level) => (
          <li key={level.label} className={timeColorClass(level.value)}>
            {level.label}: {level.value}
          </li>
        ))}
      </ul>
    </article>
  )
}

export default StationCard