/** Provide the dashboard's date picker and historical compliance report. */
import { useEffect, useId, useRef, useState, type SubmitEvent } from 'react'
import { getReportData, type ReportData } from '../api/reportDataApi'
import './ComplianceReport.css'

const shiftTime = new Intl.DateTimeFormat('da-DK', {
  dateStyle: 'medium',
  timeStyle: 'short',
  timeZone: 'Europe/Copenhagen',
})

const manningPercent = new Intl.NumberFormat('da-DK', {
  style: 'percent',
  maximumFractionDigits: 1,
})

type ReportState =
  | { status: 'idle' | 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; report: ReportData }

/** Convert the API result into the dialog state for a completed request. */
async function fetchReportState(date: string, signal: AbortSignal): Promise<ReportState> {
  try {
    const report = await getReportData(date, signal)
    return { status: 'ready', report }
  } catch (error) {
    const message = error instanceof Error ? error.message : ''
    return { status: 'error', message: `Kunne ikke hente rapporten. ${message}` }
  }
}

/**
 * Track the report request and expose its state, load and reset actions.
 *
 * Ignore duplicate submissions while a request is pending. Reset aborts it
 * and clears the result. Unmount also aborts any outstanding request.
 */
function useComplianceReport() {
  const request = useRef<AbortController | null>(null)
  const [state, setState] = useState<ReportState>({ status: 'idle' })

  useEffect(() => () => request.current?.abort(), [])

  function reset() {
    request.current?.abort()
    request.current = null
    setState({ status: 'idle' })
  }

  async function load(date: string) {
    if (!date || request.current) return

    const controller = new AbortController()
    request.current = controller
    setState({ status: 'loading' })

    const result = await fetchReportState(date, controller.signal)
    if (controller.signal.aborted) return

    request.current = null
    setState(result)
  }

  return { state, load, reset }
}

/** Format the backend's 0–100 percentage or show that the scope had no running time. */
function formatManning(percent: number | null): string {
  return percent === null ? 'Ingen køretid' : manningPercent.format(percent / 100)
}

/** Show the scheduled shift in Copenhagen time and flag figures cut off before its end. */
function ReportSummary({ report }: { report: ReportData }) {
  const start = new Date(report.shift.start)
  const end = new Date(report.shift.end)
  const asOf = new Date(report.as_of)

  return (
    <section className="compliance-report-result" aria-label="Rapportresultat" aria-live="polite">
      <dl>
        <dt>Vagtperiode (dansk tid)</dt>
        <dd>
          <time dateTime={report.shift.start}>{shiftTime.format(start)}</time>
          {' – '}
          <time dateTime={report.shift.end}>{shiftTime.format(end)}</time>
        </dd>
      </dl>
      {asOf < end && (
        <p className="compliance-report-partial">
          Tallene dækker kun en del af vagten frem til{' '}
          <time dateTime={report.as_of}>{shiftTime.format(asOf)}</time>.
        </p>
      )}
      <dl>
        <dt>Bemanding, alle linjer</dt>
        <dd>{formatManning(report.manning_percent)}</dd>
        <dt>Bemanding, M1/M2</dt>
        <dd>{formatManning(report.m1m2_manning_percent)}</dd>
        <dt>Bemanding, M3/M4</dt>
        <dd>{formatManning(report.m3m4_manning_percent)}</dd>
      </dl>
    </section>
  )
}

/**
 * Render the report button and its local shift date dialog.
 *
 * Fetch only on submit and show loading, failure or report details in the dialog.
 * Closing the dialog clears the result and keeps the selected date. Closing or
 * unmounting cancels any pending request.
 */
export default function ComplianceReport() {
  const titleId = useId()
  const dialog = useRef<HTMLDialogElement>(null)
  const [date, setDate] = useState('')
  const { state, load, reset } = useComplianceReport()
  const isLoading = state.status === 'loading'

  function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault()
    void load(date)
  }

  return (
    <>
      <button className="topbar-button" type="button" aria-haspopup="dialog"
        onClick={() => dialog.current?.showModal()}>
        Compliance report
      </button>
      <dialog className="compliance-report-dialog" ref={dialog} aria-labelledby={titleId}
        onClose={reset}>
        <h2 id={titleId}>Compliance report</h2>
        <form className="compliance-report-form" onSubmit={handleSubmit}>
          <label>
            Vagtens lokale startdato
            <input
              type="date"
              value={date}
              required
              autoFocus
              disabled={isLoading}
              onChange={(event) => {
                setDate(event.currentTarget.value)
                reset()
              }}
            />
          </label>
          <div className="compliance-report-actions">
            <button type="button" onClick={() => dialog.current?.close()}>Luk</button>
            <button type="submit" disabled={!date || isLoading}>Hent rapport</button>
          </div>
        </form>
        {isLoading && <p role="status">Henter rapport…</p>}
        {state.status === 'error' && <p role="alert">{state.message}</p>}
        {state.status === 'ready' && <ReportSummary report={state.report} />}
      </dialog>
    </>
  )
}
