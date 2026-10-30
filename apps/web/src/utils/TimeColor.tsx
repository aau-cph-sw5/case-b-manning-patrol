import type { StationLevel } from "../data/mockData"
import { LEVEL_DEADLINES } from "../data/mockDeadlines"
import { BsEmojiFrown, BsEmojiNeutral, BsEmojiSmile } from 'react-icons/bs'
import type { IconType } from 'react-icons'

/** CSS class that colours a level's row by risk: ok, at risk or overdue. */
export type TimeColor = 'row-green' | 'row-yellow' | 'row-red'

/** Map each risk colour to the emoji icon shown in front of the row. */
export const STATUS_ICONS: Record<TimeColor, IconType> = {
  'row-green': BsEmojiSmile,
  'row-yellow': BsEmojiNeutral,
  'row-red': BsEmojiFrown,
}

/** One minute in milliseconds. */
const MIN = 60000
const PATROL_INTERVAL_MIN = 60

/**
 * Return the minutes until the area must be patrolled again.
 *
 * Negative means overdue. The result is fractional; use
 * {@link formatRemaining} to display it. A manned area always returns the
 * full patrol interval.
 *
 * The deadline is looked up in the mock {@link LEVEL_DEADLINES} under
 * `${stationCode}_${level.label}`; `level.lastPatrolAt` is not used. A level
 * with no entry there gets `now` as its deadline and returns 0, so it counts
 * as overdue.
 *
 * @param now - Current time in ms since epoch.
 */
export function remainingMinutes(level: StationLevel, now: number, stationCode: string): number {
  if (level.manned) {
    return PATROL_INTERVAL_MIN
  }
  const key = `${stationCode}_${level.label}`
  const deadline = LEVEL_DEADLINES[key] || now
  return (deadline - now) / MIN
}

/**
 * Format remaining minutes for display.
 *
 * Time left rounds up ("12 min"). Overdue by a full minute or more shows the
 * whole minutes overdue with a plus ("+3 min"). Anything from 0 down to just
 * above -1 shows "0 min".
 */
export function formatRemaining(minutes: number): string {
  if (minutes <= -1) {
    return `+${Math.floor(Math.abs(minutes))} min`
  }
  if (minutes <= 0) {
    return '0 min'
  }
  return `${Math.ceil(minutes)} min`
}

/**
 * Return the risk colour class for a level's remaining minutes.
 *
 * Zero or less is red (overdue), up to and including `riskTime` is yellow
 * (at risk), above it is green. The result is always a {@link TimeColor};
 * callers cast it.
 *
 * @param riskTime - At-risk threshold in minutes.
 */
export function timeColorClass(minutes: number, riskTime: number = 10): string {
  if (minutes <= 0) {
    return 'row-red'
  }
  return minutes > riskTime ? 'row-green' : 'row-yellow'
}

export default timeColorClass
