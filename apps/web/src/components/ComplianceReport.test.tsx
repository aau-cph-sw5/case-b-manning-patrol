// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import Dashboard from './Dashboard'

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
const figures = { manning_percent: 70, m1m2_manning_percent: 80, m3m4_manning_percent: null }

afterEach(() => {
  cleanup()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

async function renderDashboard() {
  const view = render(<Dashboard />)
  await screen.findByText('I risiko denne vagt (0)')
  return view
}

async function openReport() {
  vi.stubEnv('VITE_ROLE', 'operations_administrator')
  const view = await renderDashboard()
  const dialog = view.container.querySelector('dialog')!
  // jsdom does not implement the native modal methods.
  dialog.showModal = () => { dialog.open = true }
  fireEvent.click(screen.getByRole('button', { name: 'Compliance report' }))
  return within(screen.getByRole('dialog', { name: 'Compliance report' }))
}

it.each([undefined, 'controlRoomOperator', 'it_administrator'])('hides the button for %s', async (role) => {
  vi.stubEnv('VITE_ROLE', role)
  await renderDashboard()
  expect(screen.queryByRole('button', { name: 'Compliance report' })).toBeNull()
})

it('sends the selected local date unchanged and refreshes a partial report', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(Response.json({ shift, ...figures, as_of: '2026-11-03T10:00:00Z' }))
    .mockResolvedValueOnce(Response.json({ shift, ...figures, as_of: shift.end, manning_percent: 75 }))
  vi.stubGlobal('fetch', fetchMock)
  const report = await openReport()
  fireEvent.change(report.getByLabelText('Vagtens lokale startdato'), { target: { value: '2026-11-03' } })
  const submit = report.getByRole('button', { name: 'Hent rapport' })
  fireEvent.click(submit)

  const partialNotice = await report.findByText(/Tallene dækker kun en del af vagten/)
  expect(partialNotice.querySelector('time')?.textContent).toMatch(/11\.00/)
  expect(report.getByText(/3\. nov\. 2026, 00\.00/).getAttribute('datetime')).toBe(shift.start)
  expect(report.getByText(/3\. nov\. 2026, 23\.59/).getAttribute('datetime')).toBe(shift.end)
  expect(report.getByText(/70\s*%/)).toBeTruthy()
  expect(report.getByText('Ingen køretid')).toBeTruthy()

  fireEvent.click(submit)
  expect(await report.findByText(/75\s*%/)).toBeTruthy()
  expect(report.queryByText(/Tallene dækker kun en del af vagten/)).toBeNull()
  expect(fetchMock).toHaveBeenCalledTimes(2)
  for (const [url, request] of fetchMock.mock.calls) {
    expect(url).toBe('/api/v2/report_data?date=2026-11-03')
    expect(request.headers.get('Authorization')).toBe('Bearer operations_administrator')
    expect(request.cache).toBe('no-store')
  }
})

it('ignores a delayed response after closing and reopening the dialog', async () => {
  let finishFirstRequest!: (response: Response) => void
  const firstResponse = new Promise<Response>((resolve) => {
    finishFirstRequest = resolve
  })
  const fetchMock = vi.fn()
    .mockReturnValueOnce(firstResponse)
    .mockResolvedValueOnce(Response.json({ shift, ...figures, as_of: shift.end, manning_percent: 75 }))
  vi.stubGlobal('fetch', fetchMock)
  const report = await openReport()
  const dialog = screen.getByRole<HTMLDialogElement>('dialog', { name: 'Compliance report' })
  dialog.close = () => {
    dialog.open = false
    fireEvent(dialog, new Event('close'))
  }
  const date = report.getByLabelText<HTMLInputElement>('Vagtens lokale startdato')
  fireEvent.change(date, { target: { value: '2026-11-03' } })
  fireEvent.click(report.getByRole('button', { name: 'Hent rapport' }))
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
  expect(report.getByRole('status').textContent).toContain('Henter rapport')

  fireEvent.click(report.getByRole('button', { name: 'Luk' }))
  expect(fetchMock.mock.calls[0][1].signal.aborted).toBe(true)
  fireEvent.click(screen.getByRole('button', { name: 'Compliance report' }))
  expect(date.value).toBe('2026-11-03')
  fireEvent.click(report.getByRole('button', { name: 'Hent rapport' }))
  expect(await report.findByText(/75\s*%/)).toBeTruthy()

  await act(async () => {
    finishFirstRequest(Response.json({ shift, ...figures, as_of: shift.end }))
  })
  expect(report.getByText(/75\s*%/)).toBeTruthy()
  expect(report.queryByText(/70\s*%/)).toBeNull()
})

it.each([
  [401, null, 'Din adgang kunne ikke bekræftes (401).'],
  [403, null, 'Du har ikke adgang til rapporten (403).'],
  [400, '{"code":"400","message":"Vagten er endnu ikke startet."}', 'Vagten er endnu ikke startet.'],
  [500, 'Invalid JSON', 'Serveren svarede med HTTP 500.'],
])('shows the report error when the backend returns %d', async (status, body, message) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(body, { status })))
  const report = await openReport()
  fireEvent.change(report.getByLabelText('Vagtens lokale startdato'), { target: { value: '2026-11-03' } })
  fireEvent.click(report.getByRole('button', { name: 'Hent rapport' }))
  expect((await report.findByRole('alert')).textContent).toContain(message)
  expect(report.queryByRole('region', { name: 'Rapportresultat' })).toBeNull()
})
