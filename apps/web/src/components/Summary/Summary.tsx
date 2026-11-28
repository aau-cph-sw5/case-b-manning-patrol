import './Summary.css'
import { useState } from 'react'
import ButtonToDashboard from './ButtonToDashboard.tsx'
import DateSelector from './DateSelector.tsx'
import ShiftDetails from './ShiftDetails.tsx'

//const summary should be replaced with backend data
export default function Summary() {
  const today = new Date().toISOString().slice(0, 10)
  const [selectedDate, setSelectedDate] = useState(today)
  const summary = {
  shift_started_at: `${selectedDate} kl. 00.00`,
  shift_finished_at: `${selectedDate} kl. 06.00`,
  report_generated_at: 'genereret nu',
}

  return (
    <div className="summary-page">
      <header className="topbar">
        <div className="brand">
          <span className="logo">METRO</span>
        </div>
        <ButtonToDashboard />
        <DateSelector
          value={selectedDate}
          maxDate={today}
          onDateChange={setSelectedDate}
        />
      </header>
      <main className="summary-content">
        <ShiftDetails
          shiftDate={selectedDate}
          startedAt={summary.shift_started_at}
          finishedAt={summary.shift_finished_at}
          reportGeneratedAt={summary.report_generated_at}
        />
      </main>
    </div>
  )
}