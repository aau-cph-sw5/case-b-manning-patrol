/** Provide the historical compliance report and its local shift date picker. */
import { useEffect, useRef, useState } from 'react'
import { canViewHistoricalData } from '../api/auth'
import { getReportData, type ReportData } from '../api/reportDataApi'
import ComplianceReportResults from './ComplianceReportResults'
import ButtonToDashboard from './Summary/ButtonToDashboard'
import './ComplianceReport.css'

type ReportState =
  | { status: 'idle' | 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; report: ReportData }

function ReportPicker() {
  const request = useRef<AbortController | null>(null)
  const [date, setDate] = useState('')
  const [state, setState] = useState<ReportState>({ status: 'idle' })

  useEffect(() => () => request.current?.abort(), [])

  async function loadReport(selectedDate: string) {
    request.current?.abort()
    request.current = null
    if (!selectedDate) {
      setState({ status: 'idle' })
      return
    }

    const controller = new AbortController()
    request.current = controller
    setState({ status: 'loading' })
    try {
      const report = await getReportData(selectedDate, controller.signal)
      if (!controller.signal.aborted) setState({ status: 'ready', report })
    } catch (error) {
      if (!controller.signal.aborted) {
        const detail = error instanceof Error ? ` ${error.message}` : ''
        setState({ status: 'error', message: `Kunne ikke hente rapporten.${detail}` })
      }
    } finally {
      if (request.current === controller) request.current = null
    }
  }

  return (
    <>
      <form className="compliance-report-picker" onSubmit={(event) => {
        event.preventDefault()
        void loadReport(date)
      }}>
        <label>
          Nattevagtens lokale startdato
          <input
            type="date"
            value={date}
            required
            onChange={(event) => {
              const selectedDate = event.currentTarget.value
              setDate(selectedDate)
              void loadReport(selectedDate)
            }}
          />
        </label>
        <button type="submit" disabled={!date || state.status === 'loading'}>Hent igen</button>
      </form>
      {state.status === 'idle' && <p>Vælg datoen, hvor nattevagten starter i dansk tid.</p>}
      {state.status === 'loading' && <p role="status">Henter rapport…</p>}
      {state.status === 'error' && <p role="alert">{state.message}</p>}
      {state.status === 'ready' && <ComplianceReportResults report={state.report} />}
    </>
  )
}

/**
 * Render the historical report page and allow date selection for Operations Administrators.
 *
 * Selecting or refreshing a date loads a new report. A new selection or
 * leaving the page cancels the pending request.
 */
export default function ComplianceReport() {
  return (
    <div className="compliance-report-page">
      <header className="topbar">
        <div className="brand"><span className="logo">METRO</span></div>
        <ButtonToDashboard />
      </header>
      <main className="compliance-report-main">
        <h1>Compliance report</h1>
        {canViewHistoricalData()
          ? <ReportPicker />
          : <p role="alert">Historiske rapporter kræver adgang som Operations Administrator.</p>}
      </main>
    </div>
  )
}
