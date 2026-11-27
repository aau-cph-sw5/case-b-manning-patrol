// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import App from '../App'

vi.mock('../hooks/useDashboardStream', () => ({
  useDashboardStream: () => ({ dashboard: null, isLoading: false, error: null, lastUpdated: null }),
}))
vi.mock('../hooks/useTrainStream', () => ({ useTrainStream: () => ({ trainsUpdate: null }) }))
vi.mock('../api/configApi', () => ({
  getAtRiskThreshold: () => Promise.resolve({ at_risk_threshold_minutes: 10 }),
  setAtRiskThreshold: vi.fn(),
}))
vi.mock('../api/atRiskCountApi', () => ({
  getAtRiskCount: () => Promise.resolve({ episodes: 0 }),
}))

const shift = { start: '2026-11-02T23:00:00Z', end: '2026-11-03T22:59:00Z' }
const asOf = '2026-11-03T10:00:00Z'
const report = {
  shift,
  as_of: asOf,
  known_at: null,
  manning_percent: 78,
  m1m2_manning_percent: 69.999,
  m3m4_manning_percent: 84,
  trains: [{
    train_id: '7a912fbb-1ce7-4dc2-b870-0ef1934c75e6',
    slug: 'train-1',
    line: ['M1', 'M2'],
    manned_ratio: 0.625,
    manned_now: false,
    manned_time: 4500,
    running_time: 7200,
  }],
  stations: [{
    station_id: 'STN-001',
    name: 'Vestamager',
    line: ['M1'],
    areas: [
      { area_id: 'PA-001-P', name: 'Platform', line: ['M1'], area_type: 'platform',
        covered_now: true, overdue_at: null, last_covered_at: null, coverage_status: 'compliant' },
      { area_id: 'PA-001-C', name: 'Concourse', line: ['M1'], area_type: 'concourse',
        covered_now: false, overdue_at: asOf, last_covered_at: null, coverage_status: 'overdue' },
    ],
  }],
}

afterEach(() => {
  cleanup()
  window.history.replaceState({}, '', '/')
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

function openReport(path = '/compliance-report') {
  vi.stubEnv('VITE_ROLE', 'operations_administrator')
  window.history.replaceState({}, '', path)
  render(<App />)
}

function selectDate(value = '2026-11-03') {
  fireEvent.change(screen.getByLabelText('Nattevagtens lokale startdato'), { target: { value } })
}

it.each([undefined, 'controlRoomOperator', 'it_administrator'])('denies report access for %s', async (role) => {
  vi.stubEnv('VITE_ROLE', role)
  const fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  const dashboard = render(<App />)
  await screen.findByText('I risiko denne vagt (0)')
  expect(screen.queryByRole('link', { name: 'Compliance report' })).toBeNull()
  dashboard.unmount()

  window.history.replaceState({}, '', '/compliance-report')
  render(<App />)
  expect(screen.getByRole('alert').textContent).toContain('Operations Administrator')
  expect(screen.queryByLabelText('Nattevagtens lokale startdato')).toBeNull()
  expect(fetchMock).not.toHaveBeenCalled()
})

it('links from the dashboard to the report and assesses each line group before rounding', async () => {
  const fetchMock = vi.fn().mockResolvedValue(Response.json(report))
  vi.stubGlobal('fetch', fetchMock)
  vi.stubEnv('VITE_ROLE', 'operations_administrator')
  const dashboard = render(<App />)
  await screen.findByText('I risiko denne vagt (0)')
  const path = screen.getByRole('link', { name: 'Compliance report' }).getAttribute('href')!
  expect(path).toBe('/compliance-report')
  dashboard.unmount()

  openReport(path)
  expect(screen.getByRole('link', { name: 'Dashboard' }).getAttribute('href')).toBe('/')
  selectDate()
  expect(screen.getByRole('status').textContent).toContain('Henter rapport')
  const period = await screen.findByRole('region', { name: 'Rapportperiode' })
  expect(within(period).getByText(/Delvis rapport/)).toBeTruthy()
  expect(within(period).getByText(/3\. nov\. 2026, 00\.00\.00/).getAttribute('datetime')).toBe(shift.start)
  expect(within(period).getByText(/3\. nov\. 2026, 23\.59\.00/).getAttribute('datetime')).toBe(shift.end)
  expect(within(period).getByText(/3\. nov\. 2026, 11\.00\.00/).getAttribute('datetime')).toBe(asOf)

  const manning = within(screen.getByRole('region', { name: 'Togbemanding' }))
  expect(manning.getByText('Bemandingskravet er ikke opfyldt')).toBeTruthy()
  expect(manning.getByText(/< 70\s*%/)).toBeTruthy()
  expect(manning.getByText(/78\s*%/)).toBeTruthy()

  const trains = within(screen.getByRole('table', { name: 'Togdetaljer' }))
  expect(trains.getByRole('row', { name: /train-1 M1, M2 1 t 15 min 0 sek 2 t 0 min 0 sek 62,5\s*%/ })).toBeTruthy()
  const patrol = screen.getByRole('table', { name: 'Stationspatruljering', description: /11\.00\.00/ })
  expect(within(patrol).getByRole('row', { name: 'Vestamager Platform Inden for fristen' })).toBeTruthy()
  expect(within(patrol).getByRole('row', { name: 'Vestamager Concourse Overskredet' })).toBeTruthy()

  const [url, request] = fetchMock.mock.calls[0]
  expect(url).toBe('/api/v2/report_data?date=2026-11-03')
  expect(request.headers.get('Authorization')).toBe('Bearer operations_administrator')
  expect(request.cache).toBe('no-store')
})

it('treats no running time separately and refreshes the date with no query cutoff', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(Response.json({
      ...report, as_of: shift.end, manning_percent: 84, m1m2_manning_percent: null,
    }))
    .mockResolvedValueOnce(Response.json({
      ...report, as_of: shift.end, m1m2_manning_percent: 70, m3m4_manning_percent: 70,
    }))
  vi.stubGlobal('fetch', fetchMock)
  openReport()
  selectDate()
  expect(await screen.findByText('Ingen driftstid')).toBeTruthy()
  expect(screen.getByText(/Bemandingskravet kan ikke vurderes/)).toBeTruthy()
  expect(screen.queryByText(/Delvis rapport/)).toBeNull()

  fireEvent.click(screen.getByRole('button', { name: 'Hent igen' }))
  expect(await screen.findByText('Bemandingskravet er opfyldt')).toBeTruthy()
  expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
    '/api/v2/report_data?date=2026-11-03',
    '/api/v2/report_data?date=2026-11-03',
  ])
})

it('shows empty data for a shift with no trains or patrol areas', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({
    ...report, trains: [], stations: [], manning_percent: null,
    m1m2_manning_percent: null, m3m4_manning_percent: null,
  })))
  openReport()
  selectDate()

  expect(await screen.findByText('Ingen togdata for vagten.')).toBeTruthy()
  expect(screen.getByText('Ingen patruljeområder i rapporten.')).toBeTruthy()
  expect(screen.getAllByText('Ingen driftstid')).toHaveLength(3)
})

it.each([
  [400, 'Vagten på den valgte dato er endnu ikke startet'],
  [401, 'Din adgang kunne ikke bekræftes'],
  [403, 'Du har ikke adgang til rapporten'],
  [500, 'Serveren svarede med HTTP 500'],
])('shows a report error when the backend returns %d', async (status, message) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(null, { status })))
  openReport()
  selectDate()
  expect((await screen.findByRole('alert')).textContent).toContain(message)
  expect(screen.queryByRole('region', { name: 'Rapportperiode' })).toBeNull()
})

it('ignores a delayed response for the previous date', async () => {
  let resolvePrevious: (value: Response) => void = () => {}
  const previous = new Promise<Response>((resolve) => { resolvePrevious = resolve })
  const fetchMock = vi.fn()
    .mockReturnValueOnce(previous)
    .mockResolvedValueOnce(Response.json({ ...report, manning_percent: 91 }))
  vi.stubGlobal('fetch', fetchMock)
  openReport()
  selectDate('2026-11-02')
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
  selectDate('2026-11-03')
  expect(await screen.findByText(/91\s*%/)).toBeTruthy()
  expect(fetchMock.mock.calls[0][1].signal.aborted).toBe(true)

  await act(async () => { resolvePrevious(Response.json(report)) })
  expect(screen.getByText(/91\s*%/)).toBeTruthy()
  expect(screen.queryByText(/78\s*%/)).toBeNull()
})
