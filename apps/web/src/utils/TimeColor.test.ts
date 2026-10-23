import { describe, expect, it } from 'vitest'
import type { StationLevel } from '../data/mockData'
import { AttentionTime } from '../settings'
import {
  formatRemaining,
  remainingMinutes,
  timeColorClass,
} from './TimeColor'

const MIN = 60000
const NOW = Date.UTC(2026, 0, 1, 12, 0)

function level(minutesSincePatrol: number, manned = false): StationLevel {
  return {
    label: 'Platform',
    lastPatrolAt: NOW - minutesSincePatrol * MIN,
    manned,
  }
}

describe('remainingMinutes', () => {
  it('is the full interval right after a patrol', () => {
    expect(remainingMinutes(level(0), NOW)).toBe(60)
  })

  it('counts down as time passes', () => {
    expect(remainingMinutes(level(15), NOW)).toBe(45)
  })

  it('goes negative once the patrol is overdue', () => {
    expect(remainingMinutes(level(75), NOW)).toBe(-15)
  })

  it('stays at the full interval while the area is manned', () => {
    expect(remainingMinutes(level(90, true), NOW)).toBe(60)
  })
})

describe('formatRemaining', () => {
  it('rounds remaining time up to whole minutes', () => {
    expect(formatRemaining(44.2)).toBe('45 min')
  })

  it('shows zero as 0 min', () => {
    expect(formatRemaining(0)).toBe('0 min')
  })

  it('shows overdue time with a plus sign', () => {
    expect(formatRemaining(-3.5)).toBe('+4 min')
  })

  it('shows a fraction of a minute overdue as +1 min', () => {
    expect(formatRemaining(-0.1)).toBe('+1 min')
  })
})

describe('timeColorClass', () => {
  it('is red when overdue', () => {
    expect(timeColorClass(-0.1)).toBe('row-red')
  })

  it('is yellow when due now', () => {
    expect(timeColorClass(0)).toBe('row-yellow')
  })

  it('is yellow at the attention threshold', () => {
    expect(timeColorClass(AttentionTime)).toBe('row-yellow')
  })

  it('is green above the attention threshold', () => {
    expect(timeColorClass(AttentionTime + 0.1)).toBe('row-green')
  })
})
