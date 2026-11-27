/** Display the shift window, train staffing and evaluated station coverage. */
import type { ReportData } from '../api/reportDataApi'

const shiftTime = new Intl.DateTimeFormat('da-DK', {
  dateStyle: 'medium',
  timeStyle: 'medium',
  timeZone: 'Europe/Copenhagen',
})
const percentage = new Intl.NumberFormat('da-DK', { maximumFractionDigits: 2 })
const manningTarget = 70

function ReportTime({ value }: { value: string }) {
  return <time dateTime={value}>{shiftTime.format(new Date(value))}</time>
}

function formatManning(value: number | null): string {
  return value === null ? 'Ingen driftstid' : `${percentage.format(value)}\u00a0%`
}

/** Keep a failing line group's displayed percentage below the target even when rounding. */
function formatLineGroupManning(value: number | null): string {
  const formatted = formatManning(value)
  const target = formatManning(manningTarget)
  return value !== null && value < manningTarget && formatted === target ? `< ${target}` : formatted
}

function formatDuration(seconds: number): string {
  const wholeSeconds = Math.round(seconds)
  const hours = Math.floor(wholeSeconds / 3600)
  const minutes = Math.floor(wholeSeconds / 60) % 60
  return `${hours} t ${minutes} min ${wholeSeconds % 60} sek`
}

function isBelowTarget(value: number | null): boolean {
  return value !== null && value < manningTarget
}

/** Fail if either group's measured result is below target, even when the other has no running time. */
function manningStatus(groups: { label: string; value: number | null }[]) {
  if (groups.some(({ value }) => isBelowTarget(value))) {
    return { tone: 'fail', text: 'Bemandingskravet er ikke opfyldt' }
  }
  if (groups.some(({ value }) => value === null)) {
    return { tone: 'pending', text: 'Bemandingskravet kan ikke vurderes for begge linjegrupper' }
  }
  return { tone: 'pass', text: 'Bemandingskravet er opfyldt' }
}

function ManningOverview({ report }: { report: ReportData }) {
  const groups = [
    { label: 'M1/M2', value: report.m1m2_manning_percent },
    { label: 'M3/M4', value: report.m3m4_manning_percent },
  ]
  const status = manningStatus(groups)

  return (
    <section className="card compliance-report-card" aria-labelledby="report-manning">
      <h2 id="report-manning">Togbemanding</h2>
      <p>Begge linjegrupper skal hver nå mindst 70 %.</p>
      <p className="compliance-report-status" data-tone={status.tone}>{status.text}</p>
      <dl className="compliance-report-metrics">
        {groups.map(({ label, value }) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{formatLineGroupManning(value)}</dd>
            {value !== null && <dd>{isBelowTarget(value) ? 'Under kravet' : 'Opfylder kravet'}</dd>}
          </div>
        ))}
        <div>
          <dt>Flåden samlet</dt>
          <dd>{formatManning(report.manning_percent)}</dd>
          <dd>Til orientering</dd>
        </div>
      </dl>
    </section>
  )
}

function TrainDetails({ trains }: { trains: ReportData['trains'] }) {
  return (
    <section className="card compliance-report-card" aria-labelledby="report-trains">
      <h2 id="report-trains">Togdetaljer</h2>
      {trains.length === 0 ? <p>Ingen togdata for vagten.</p> : (
        <div className="compliance-report-table">
          <table aria-labelledby="report-trains">
            <thead>
              <tr>
                <th scope="col">Tog</th>
                <th scope="col">Linjer</th>
                <th scope="col">Bemandet tid</th>
                <th scope="col">Driftstid</th>
                <th scope="col">Bemandingsandel</th>
              </tr>
            </thead>
            <tbody>
              {trains.map((train) => (
                <tr key={train.train_id}>
                  <th scope="row">{train.slug}</th>
                  <td>{train.line.join(', ') || '—'}</td>
                  <td>{formatDuration(train.manned_time)}</td>
                  <td>{formatDuration(train.running_time)}</td>
                  <td>{formatManning(train.manned_ratio === null ? null : train.manned_ratio * 100)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

function PatrolDetails({ stations, asOf }: { stations: ReportData['stations']; asOf: string }) {
  const rows = stations.flatMap((station) => station.areas.map((area) => ({ station, area })))

  return (
    <section className="card compliance-report-card" aria-labelledby="report-patrol">
      <h2 id="report-patrol">Stationspatruljering</h2>
      <p id="report-patrol-time">Status pr. område ved <ReportTime value={asOf} /> (dansk tid).</p>
      {rows.length === 0 ? <p>Ingen patruljeområder i rapporten.</p> : (
        <div className="compliance-report-table">
          <table aria-labelledby="report-patrol" aria-describedby="report-patrol-time">
            <thead>
              <tr>
                <th scope="col">Station</th>
                <th scope="col">Område</th>
                <th scope="col">Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ station, area }) => (
                <tr key={`${station.station_id}:${area.area_id}`}>
                  <td>{station.name}</td>
                  <td>{area.name}</td>
                  <td>{area.coverage_status === 'overdue' ? 'Overskredet' : 'Inden for fristen'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

/** Show the scheduled period and mark snapshots taken before the shift ended. */
export default function ComplianceReportResults({ report }: { report: ReportData }) {
  const isPartial = Date.parse(report.as_of) < Date.parse(report.shift.end)

  return (
    <div className="compliance-report-results">
      <section className="card compliance-report-card" aria-labelledby="report-period">
        <h2 id="report-period">Rapportperiode</h2>
        <dl className="compliance-report-period">
          <div>
            <dt>Vagtperiode (dansk tid)</dt>
            <dd><ReportTime value={report.shift.start} /> – <ReportTime value={report.shift.end} /></dd>
          </div>
          <div>
            <dt>Vurderingstidspunkt (dansk tid)</dt>
            <dd><ReportTime value={report.as_of} /></dd>
          </div>
        </dl>
        {isPartial && (
          <p className="compliance-report-status" data-tone="pending">
            Delvis rapport. Tallene dækker kun vagten frem til vurderingstidspunktet.
          </p>
        )}
      </section>
      <ManningOverview report={report} />
      <TrainDetails trains={report.trains} />
      <PatrolDetails stations={report.stations} asOf={report.as_of} />
    </div>
  )
}
