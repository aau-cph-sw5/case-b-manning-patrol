import './Summary.css'
import ButtonToDashboard from './ButtonToDashboard.tsx'
import TrainManningPies from './TrainManningPies.tsx'

/** Shift summary page: train manning pies on the left, station statistics on the right. */
export default function Summary() {
  return (
    <div className="summary-page">
      <header className="topbar">
        <div className="brand">
          <span className="logo">METRO</span>
        </div>
        <ButtonToDashboard />
      </header>
      <main className="summary-content">
        <TrainManningPies />
        <section className="summary-stations">
          {/* Date picker and the "Overskrevet station bemandelse" bar chart belong here (separate issue) */}
        </section>
      </main>
    </div>
  )
}
