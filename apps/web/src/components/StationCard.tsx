import type { Station } from '../data/mockData'

export function timeColorClass(value: string): string {
  if (value.startsWith('+')) {
    return 'row-red'
  }
  const minutes = Number.parseFloat(value)
  return minutes > 10 ? 'row-green' : 'row-yellow'
}

export function PersonIcon() {
  return (
    <svg
      className="person-icon"
      viewBox="0 0 12 20"
      width="11"
      height="18"
      aria-hidden="true"
    >
      <circle cx="6" cy="3" r="2.6" fill="currentColor" />
      <path
        d="M6 6.5 V13 M1.5 8.5 H10.5 M6 13 L2.5 19 M6 13 L9.5 19"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  )
}

function StationCard({ station }: { station: Station }) {
  return (
    <article className="card station-card">
      <h2>{station.name}</h2>
      <ul className="levels">
        {station.levels.map((level) => (
          <li key={level.label} className={timeColorClass(level.value)}>
            {station.person && level.label === 'Platform' && <PersonIcon />}
            {level.label}: {level.value}
          </li>
        ))}
      </ul>
    </article>
  )
}

export default StationCard