import type { StationLevel } from "../data/mockData"
import { LEVEL_DEADLINES } from "../data/mockDeadlines"
import { BsEmojiFrown, BsEmojiNeutral, BsEmojiSmile } from 'react-icons/bs'
import type { IconType } from 'react-icons'

export type TimeColor = 'row-green' | 'row-yellow' | 'row-red'

export const STATUS_ICONS: Record<TimeColor, IconType> = {
  'row-green': BsEmojiSmile,
  'row-yellow': BsEmojiNeutral,
  'row-red': BsEmojiFrown,
}

const MIN = 60000 //ms
const PATROL_INTERVAL_MIN = 60

// minutes until the area must be patrolled again; negative means overdue.
// a manned area is frozen at the full interval.
export function remainingMinutes(level: StationLevel, now: number, stationCode: string): number {
  if (level.manned) {
    return PATROL_INTERVAL_MIN
  }
  const key = `${stationCode}_${level.label}`
  const deadline = LEVEL_DEADLINES[key] || now
  return (deadline - now) / MIN
}

export function formatRemaining(minutes: number): string {
  if (minutes <= -1) {
    return `+${Math.floor(Math.abs(minutes))} min`
  }
  if (minutes <= 0) {
    return '0 min'
  }
  return `${Math.ceil(minutes)} min`
}

export function timeColorClass(minutes: number, riskTime: number = 10): string {
  if (minutes <= 0) {
    return 'row-red'
  }
  return minutes > riskTime ? 'row-green' : 'row-yellow'
}

export default timeColorClass
