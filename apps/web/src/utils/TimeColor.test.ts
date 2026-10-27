import { describe, expect, it, vi } from 'vitest'
import type { StationLevel } from '../data/mockData'
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

vi.mock('../data/mockDeadlines', () => ({
  LEVEL_DEADLINES: {
    TST_Perron: NOW + 60 * MIN,
    TST_Forhal: NOW + 60 * MIN,
    'TST_Perron 1': NOW,
  },
}))

function level(label: string, manned = false): StationLevel {
  return { label, lastPatrolAt: NOW, manned }
}

describe('remainingMinutes', () => {
  it('is the full interval at the start', () => {
    expect(remainingMinutes(level('Perron'), NOW, 'TST')).toBe(60)
  })

  it('counts down as time passes', () => {
    expect(remainingMinutes(level('Perron'), NOW + 15 * MIN, 'TST')).toBe(45)
  })

  it('goes negative once the deadline has passed', () => {
    expect(remainingMinutes(level('Forhal'), NOW + 75 * MIN, 'TST')).toBe(-15)
  })

  it('is zero exactly at the deadline', () => {
    expect(remainingMinutes(level('Perron 1'), NOW, 'TST')).toBe(0)
  })

  it('looks up the deadline by station code and level label', () => {
    expect(remainingMinutes(level('Perron'), NOW, 'XYZ')).toBe(0)
  })

  it('is zero when the level has no deadline', () => {
    expect(remainingMinutes(level('Unknown'), NOW, 'TST')).toBe(0)
  })

  it('stays at the full interval while the area is manned', () => {
    expect(remainingMinutes(level('Forhal', true), NOW, 'TST')).toBe(60)
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
