interface StationLevel {
  label: string
  value: string
}

interface Station {
  code: string
  name: string
  person?: boolean
  levels: StationLevel[]
}

interface AttentionItem {
  code: string
  value: string
  person?: boolean
}

const STATIONS: Station[] = [
  {
    code: 'VAN',
    name: 'Vanløse',
    levels: [{ label: 'Platform', value: '10 min' }],
  },
  {
    code: 'FLT',
    name: 'Flintholm',
    person: true,
    levels: [
      { label: 'Platform', value: '6 min' },
      { label: 'Concourse', value: '+5 min' },
    ],
  },
  {
    code: 'LIN',
    name: 'Lindevang',
    levels: [
      { label: 'Platform', value: '48 min' },
      { label: 'Concourse', value: '45 min' },
    ],
  },
  {
    code: 'FAS',
    name: 'Fasanvej',
    levels: [
      { label: 'Platform', value: '49 min' },
      { label: 'Concourse', value: '31 min' },
    ],
  },
  {
    code: 'KNG',
    name: 'Kongens',
    levels: [
      { label: 'Platform1', value: '19 min' },
      { label: 'Platform2', value: '10 min' },
      { label: 'Concourse', value: '23 min' },
    ],
  },
]

const ATTENTION: AttentionItem[] = [
  { code: 'FLT_CON', value: '+5 min' },
  { code: 'FLT_PLAT', value: '6 min', person: true },
  { code: 'VAN_PLAT', value: '10 min' },
  { code: 'KNG_PLAT2', value: '10 min' },
]

function timeColorClass(value: string): string {
  if (value.startsWith('+')) {
    return 'row-red'
  }
  const minutes = Number.parseFloat(value)
  return minutes > 10 ? 'row-green' : 'row-yellow'
}

function PersonIcon() {
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

function Dashboard() {
  return (
    <>
      <h1>Manning Patrol Dashboard</h1>
      <div className="dash">
        <section className="station-grid">
          {STATIONS.map((station) => (
            <StationCard key={station.code} station={station} />
          ))}
        </section>
        <aside className="card attention">
          <h2>ATTENTION ({ATTENTION.length})</h2>
          <ul className="attention-list">
            {ATTENTION.map((item) => (
              <li key={item.code} className={timeColorClass(item.value)}>
                {item.person && <PersonIcon />}
                {item.code} {item.value}
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </>
  )
}

export default Dashboard
