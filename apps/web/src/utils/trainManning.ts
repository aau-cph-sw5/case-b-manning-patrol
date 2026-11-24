/**
 * Trend logic for the train manning card: whether the manned share of
 * running time is rising, falling or flat compared with the displayed
 * percentage.
 */

/** Direction the manning percentage is heading. */
export type Trend = 'up' | 'down' | 'flat'

/** Percentage points within which the current manned share counts as flat. */
const TREND_TOLERANCE_PCT = 1

/**
 * Direction the manning percentage is heading right now.
 *
 * The percentage is manned time over running time, so it rises while the share
 * of trains manned right now is above it and falls while it is below. Within
 * {@link TREND_TOLERANCE_PCT} of it the trend is flat.
 *
 * @param percent - The displayed manning percentage (0..100).
 * @returns Null when there are no trains or no percentage yet.
 */
export function trendOf(manned: number, total: number, percent: number | null): Trend | null {
  if (total <= 0 || percent === null) return null
  const currentPct = (manned / total) * 100
  if (currentPct > percent + TREND_TOLERANCE_PCT) return 'up'
  if (currentPct < percent - TREND_TOLERANCE_PCT) return 'down'
  return 'flat'
}
