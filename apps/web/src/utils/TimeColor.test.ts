import { describe, expect, it, vi } from 'vitest'
import type { StationLevel } from '../api/dashboardMapper'
import { RiskTime } from '../settings'
import {
  formatRemaining,
  remainingMinutes,
  timeColorClass,
} from './TimeColor'

const { MIN, NOW } = vi.hoisted(() => ({
  MIN: 60000,
  NOW: Date.UTC(2026, 0, 1, 12, 0),
}))

function level(overdueAt: number | null, manned = false): StationLevel {
  return { label: 'Perron', overdueAt, manned }
}

describe('remainingMinutes', () => {
  it('is the full interval at the start', () => {
    expect(remainingMinutes(level(NOW + 60 * MIN), NOW)).toBe(60)
  })

  it('counts down as time passes', () => {
    expect(remainingMinutes(level(NOW + 60 * MIN), NOW + 15 * MIN)).toBe(45)
  })

  it('goes negative once the deadline has passed', () => {
    expect(remainingMinutes(level(NOW + 60 * MIN), NOW + 75 * MIN)).toBe(-15)
  })

  it('is zero exactly at the deadline', () => {
    expect(remainingMinutes(level(NOW), NOW)).toBe(0)
  })

  it('is zero when the level has no deadline', () => {
    expect(remainingMinutes(level(null), NOW)).toBe(0)
  })

  it('stays at the full interval while the area is manned', () => {
    expect(remainingMinutes(level(null, true), NOW)).toBe(60)
  })
})

describe('formatRemaining', () => {
  it('rounds remaining time up to whole minutes', () => {
    expect(formatRemaining(44.2)).toBe('45 min')
  })

  it('shows zero as 0 min', () => {
    expect(formatRemaining(0)).toBe('0 min')
  })

  it('shows less than a minute overdue as 0 min', () => {
    expect(formatRemaining(-0.1)).toBe('0 min')
    expect(formatRemaining(-0.9)).toBe('0 min')
  })

  it('shows exactly one minute overdue as +1 min', () => {
    expect(formatRemaining(-1)).toBe('+1 min')
  })

  it('shows overdue time with a plus sign, rounded down', () => {
    expect(formatRemaining(-3.5)).toBe('+3 min')
  })
})

describe('timeColorClass', () => {
  it('is red when overdue', () => {
    expect(timeColorClass(-0.1)).toBe('row-red')
  })

  it('is red when due now', () => {
    expect(timeColorClass(0)).toBe('row-red')
  })

  it('is yellow just before the deadline', () => {
    expect(timeColorClass(0.1)).toBe('row-yellow')
  })

  it('is yellow at the risk threshold', () => {
    expect(timeColorClass(RiskTime)).toBe('row-yellow')
  })

  it('is green above the risk threshold', () => {
    expect(timeColorClass(RiskTime + 0.1)).toBe('row-green')
  })
})
