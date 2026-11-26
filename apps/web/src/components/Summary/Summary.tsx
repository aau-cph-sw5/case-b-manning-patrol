import './Summary.css'
import ButtonToDashboard from './ButtonToDashboard.tsx'
import BarCharts from './BarCharts.tsx'

export default function Summary() {
  return (
    <div className="summary-page">
      <header className="topbar">
        <div className="brand">
          <span className="logo">METRO</span>
        </div>
        <ButtonToDashboard />
      </header>
      <BarCharts />
    </div>
  )
}