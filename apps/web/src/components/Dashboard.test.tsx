// @vitest-environment jsdom
// Dashboard with no backend connection: a stored dashboard keeps rendering
// together with an offline pill, a cold start shows a clear message instead of
// a broken view, and the pill clears when a stream event arrives again. The
// streams and REST clients are mocked, so no network is involved.
import { act, cleanup, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Dashboard as DashboardEvent } from '@/api/dashboardApi'

const {
  subscribeToDashboard,
  subscribeToTrains,
  getAtRiskThreshold,
  setAtRiskThreshold,
  getAtRiskCount,
} = vi.hoisted(() => ({
  subscribeToDashboard: vi.fn(),
  subscribeToTrains: vi.fn(),
  getAtRiskThreshold: vi.fn(),
  setAtRiskThreshold: vi.fn(),
  getAtRiskCount: vi.fn(),
}))

vi.mock('@/api/dashboardApi', () => ({ subscribeToDashboard, subscribeToTrains }))
vi.mock('@/api/configApi', () => ({ getAtRiskThreshold, setAtRiskThreshold }))
vi.mock('@/api/atRiskCountApi', () => ({ getAtRiskCount }))

import Dashboard from './Dashboard'

const STORED: DashboardEvent = {
  stations: [
    {
      station_id: 'st-1',
      name: 'Nørreport',
      areas: [
        {
          area_id: 'a-1',
          name: 'Perron 1',
          line: ['M1', 'M2'],
          area_type: 'platform',
          covered_now: true,
          overdue_at: null,
        },
      ],
    },
  ],
  time: '2026-11-23T10:00:00+01:00',
}

/** The callbacks useDashboardStream registered on the mocked dashboard stream. */
function dashboardHandlers(): [(d: DashboardEvent) => void, (e: unknown) => void] {
  return subscribeToDashboard.mock.calls[0] as [
    (d: DashboardEvent) => void,
    (e: unknown) => void,
  ]
}

beforeEach(() => {
  localStorage.clear()
  vi.spyOn(console, 'error').mockImplementation(() => {})
  subscribeToDashboard.mockReset().mockImplementation(() => () => {})
  subscribeToTrains.mockReset().mockImplementation(() => () => {})
  getAtRiskThreshold.mockReset().mockRejectedValue(new Error('network down'))
  setAtRiskThreshold.mockReset().mockRejectedValue(new Error('network down'))
  getAtRiskCount.mockReset().mockRejectedValue(new Error('network down'))
})

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('Dashboard without a backend connection', () => {
  it('keeps showing the stored dashboard with an offline pill when the stream fails', () => {
    localStorage.setItem('dashboardState', JSON.stringify(STORED))

    render(<Dashboard />)
    const [, onError] = dashboardHandlers()
    act(() => onError(new Error('SSE connection error')))

    expect(screen.getByText('Nørreport')).toBeTruthy()
    expect(screen.getByText(/Ingen forbindelse — viser seneste data/)).toBeTruthy()
  })

  it('shows a clear message and an offline pill on a cold start with no data', () => {
    render(<Dashboard />)
    const [, onError] = dashboardHandlers()
    act(() => onError(new Error('SSE connection error')))

    expect(screen.getByText(/Kunne ikke hente data/)).toBeTruthy()
    expect(screen.getByText(/Ingen forbindelse til serveren/)).toBeTruthy()
  })

  it('clears the offline pill when a stream event arrives again', () => {
    render(<Dashboard />)
    const [onMessage, onError] = dashboardHandlers()
    act(() => onError(new Error('SSE connection error')))
    expect(screen.getByText(/Ingen forbindelse/)).toBeTruthy()

    act(() => onMessage(STORED))

    expect(screen.getByText('Nørreport')).toBeTruthy()
    expect(screen.queryByText(/Ingen forbindelse/)).toBeNull()
  })
})
