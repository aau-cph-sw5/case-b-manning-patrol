import { STATIONS, ATTENTION } from '../data/mockData.tsx'
import StationCard from './StationCard.tsx'
import { timeColorClass} from '../utils/TimeColor.tsx'

import './Dashboard.css'


function Dashboard() {
  return (
    <>
      <section className="dashboard-header">
        <h1 className='dashboard-title'>Manning Patrol Dashboard</h1>
        <div className="overdue-count">Overdue: 3</div>
      </section>
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
                {item.code}: {item.value}
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </>
  )
}

export default Dashboard