// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react'
import type { ReactNode } from 'react'

import { afterEach, describe, expect, it, vi } from 'vitest'

import type { TrainsUpdate } from '@/api/dashboardApi'
import { useTrainStream } from '@/hooks/useTrainStream'

import TrainManningPies from './TrainManningPies'

vi.mock('@/hooks/useTrainStream', () => ({ useTrainStream: vi.fn() }))

vi.mock('./ManningPieChart', async () => {
  const { createElement } = await import('react')
  return {
    default: (props: { title: ReactNode; percent: number | null; size: number }) =>
      createElement(
        'div',
        {
          'data-testid': 'pie',
          'data-percent': String(props.percent),
          'data-size': String(props.size),
        },
        props.title,
      ),
  }
})

function update(overrides: Partial<TrainsUpdate> = {}): TrainsUpdate {
  return {
    trains: [],
    manning_percent: 50,
    m1m2_manning_percent: 80,
    m3m4_manning_percent: 20,
    time: '2026-11-27T01:00:00+01:00',
    ...overrides,
  }
}

function mockStream(trainsUpdate: TrainsUpdate | null, error: Error | null = null) {
  vi.mocked(useTrainStream).mockReturnValue({
    trainsUpdate,
    isLoading: false,
    error,
    lastUpdated: trainsUpdate?.time ?? null,
  })
}

function pies() {
  return screen.getAllByTestId('pie').map((pie) => ({
    title: pie.textContent,
    percent: pie.getAttribute('data-percent'),
    size: pie.getAttribute('data-size'),
  }))
}

afterEach(() => {
  cleanup()
  vi.resetAllMocks()
})

describe('TrainManningPies', () => {
  it('feeds overall, M1/M2 and M3/M4 into the right pie, in that order', () => {
    mockStream(update())
    render(<TrainManningPies />)
    expect(pies()).toEqual([
      { title: 'Tog bemandelse for alle linjer', percent: '50', size: '300' },
      { title: 'M1/M2', percent: '80', size: '160' },
      { title: 'M3/M4', percent: '20', size: '160' },
    ])
  })

  it('passes null to every pie before the first update', () => {
    mockStream(null)
    render(<TrainManningPies />)
    expect(pies().map((pie) => pie.percent)).toEqual(['null', 'null', 'null'])
  })

  it('passes null only to the group without running time', () => {
    mockStream(update({ m3m4_manning_percent: null }))
    render(<TrainManningPies />)
    expect(pies().map((pie) => pie.percent)).toEqual(['50', '80', 'null'])
  })

  it('passes 0 through as 0, not as null', () => {
    mockStream(update({ manning_percent: 0, m1m2_manning_percent: 0, m3m4_manning_percent: 0 }))
    render(<TrainManningPies />)
    expect(pies().map((pie) => pie.percent)).toEqual(['0', '0', '0'])
  })

  it('shows a notice while the stream is disconnected', () => {
    mockStream(update(), new Error('SSE connection error'))
    render(<TrainManningPies />)
    expect(screen.getByText('Forbindelsen er afbrudt, prøver igen…')).toBeTruthy()
  })

  it('shows no notice while connected', () => {
    mockStream(update())
    render(<TrainManningPies />)
    expect(screen.queryByText('Forbindelsen er afbrudt, prøver igen…')).toBeNull()
  })

  it('keeps showing the last update while disconnected', () => {
    mockStream(update(), new Error('SSE connection error'))
    render(<TrainManningPies />)
    expect(pies()[0].percent).toBe('50')
  })
})
