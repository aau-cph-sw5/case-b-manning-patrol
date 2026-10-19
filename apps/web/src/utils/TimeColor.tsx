import type { StationLevel } from '../data/mockData'

const MIN = 60000 //ms
const PATROL_INTERVAL_MIN = 60

// minutes until the area must be patrolled again; negative means overdue.
// a manned area is frozen at the full interval.
export function remainingMinutes(level: StationLevel, now: number): number {
  if (level.manned) {
    return PATROL_INTERVAL_MIN
  }
  return PATROL_INTERVAL_MIN - (now - level.lastPatrolAt) / MIN
}

export function formatRemaining(minutes: number): string {
  if (minutes < 0) {
    return `+${Math.ceil(Math.abs(minutes))} min`
  }
  return `${Math.ceil(minutes)} min`
}

export function timeColorClass(minutes: number): string {
  if (minutes < 0) {
    return 'row-red'
  }
  return minutes > 10 ? 'row-green' : 'row-yellow'
}

export default timeColorClass
