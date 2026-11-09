/** Countdown arithmetic, formatting and colour classes for the dashboard's station levels. */
import type { StationLevel } from "../api/dashboardMapper"
import { BsEmojiFrown, BsEmojiNeutral, BsEmojiSmile } from 'react-icons/bs'
import type { IconType } from 'react-icons'

/** CSS class of a level's row: green ok, yellow at risk, red overdue. */
export type TimeColor = 'row-green' | 'row-yellow' | 'row-red'

/** Face icon shown next to a level, per row colour. */
export const STATUS_ICONS: Record<TimeColor, IconType> = {
  'row-green': BsEmojiSmile,
  'row-yellow': BsEmojiNeutral,
  'row-red': BsEmojiFrown,
}

/** One minute in milliseconds. */
const MIN = 60000
/** Levels must be patrolled hourly. */
const PATROL_INTERVAL_MIN = 60

/**
 * Return the minutes until the area must be patrolled again; negative means
 * overdue.
 *
 * A manned area is frozen at the full 60-minute interval. An area with no
 * deadline counts as due right now (0), which includes an area that has never
 * been patrolled.
 */
export function remainingMinutes(level: StationLevel, now: number): number {
  if (level.manned) {
    return PATROL_INTERVAL_MIN
  }
  if (level.overdueAt === null) {
    return 0
  }
  return (level.overdueAt - now) / MIN
}

/**
 * Format remaining minutes as "12 min", or "+3 min" once overdue.
 *
 * Time left rounds up. Overdue time rounds down, so during the first minute
 * past the deadline it shows "0 min" while the row is already red.
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
 * Return the row colour class for the remaining minutes: red at 0 or below,
 * yellow up to and including `riskTime`, green above it.
 *
 * @param riskTime - At-risk threshold in minutes.
 * @returns One of the {@link TimeColor} values, typed as string, so callers
 *   cast it.
 */
export function timeColorClass(minutes: number, riskTime: number = 10): string {
  if (minutes <= 0) {
    return 'row-red'
  }
  return minutes > riskTime ? 'row-green' : 'row-yellow'
}

export default timeColorClass
