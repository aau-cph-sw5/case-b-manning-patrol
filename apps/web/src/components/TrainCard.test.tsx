// @vitest-environment jsdom
// TrainCard degradation states: loading placeholder before the first event,
// an explicit "no manning data" state when the stream errors before any data,
// the placeholder when the manning source returns no trains, and the last
// known data still shown while the stream errors.
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import TrainCard from './TrainCard'
import type { TrainsUpdate } from '../api/dashboardApi'

afterEach(cleanup)

const EMPTY: TrainsUpdate = {
  trains: [],
  manning_percent: null,
  m1m2_manning_percent: null,
  m3m4_manning_percent: null,
  time: '2026-11-23T10:00:00+01:00',
}

const WITH_TRAIN: TrainsUpdate = {
  trains: [{ train_id: 't-1', slug: 'T1', current_steward_ids: ['s-1'], line: ['M1'] }],
  manning_percent: 75,
  m1m2_manning_percent: 80,
  m3m4_manning_percent: null,
  time: '2026-11-23T10:00:00+01:00',
}

describe('TrainCard', () => {
  it('shows the loading placeholder before the first trains event', () => {
    render(<TrainCard update={null} selection="M1/M2" error={null} />)

    expect(screen.getByLabelText('Ingen tog i drift')).toBeTruthy()
  })

  it('shows an explicit empty state when the stream errors before any data arrived', () => {
    render(<TrainCard update={null} selection="M1/M2" error={new Error('SSE connection error')} />)

    expect(screen.getByRole('status').textContent).toContain('Ingen bemandingsdata')
    expect(screen.queryByLabelText('Ingen tog i drift')).toBeNull()
  })

  it('shows the placeholder when the manning source returns no trains', () => {
    render(<TrainCard update={EMPTY} selection="M1/M2" error={null} />)

    expect(screen.getByLabelText('Ingen tog i drift')).toBeTruthy()
  })

  it('keeps showing the last known update while the stream errors', () => {
    render(<TrainCard update={WITH_TRAIN} selection="M1/M2" error={new Error('SSE connection error')} />)

    expect(screen.getByText('80%')).toBeTruthy()
    expect(screen.queryByRole('status')).toBeNull()
  })

  it('renders overall and line-group percentages from the update', () => {
    render(<TrainCard update={WITH_TRAIN} selection="M1/M2" error={null} />)

    expect(screen.getByText('80%')).toBeTruthy()
    expect(screen.getByText('75%')).toBeTruthy()
  })
})
