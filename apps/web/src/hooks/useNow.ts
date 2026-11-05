/** Hook for a wall clock that ticks once per second. */
import { useEffect, useState } from 'react'

// Dev-only fake clock: append ?fakeNow=<ISO-8601 or epoch ms> to the URL to
// preview at-risk/overdue states, e.g. ?fakeNow=2026-11-01T23:50:00Z.
// Returns null outside dev mode or when the param is missing or invalid.
export function resolveFakeNow(search: string, isDev: boolean): number | null {
  if (!isDev) return null
  const param = new URLSearchParams(search).get('fakeNow')
  if (!param) return null
  const asDate = Date.parse(param)
  if (!Number.isNaN(asDate)) return asDate
  const asEpoch = Number(param)
  return Number.isFinite(asEpoch) ? asEpoch : null
}

/**
 * Return the current time in epoch ms, re-rendering the caller once per
 * second. The interval is cleared on unmount.
 */
export function useNow(): number {
  const fakeBase = resolveFakeNow(window.location.search, import.meta.env.DEV)
  const [now, setNow] = useState(() => fakeBase ?? Date.now())

  useEffect(() => {
    const offset = fakeBase === null ? 0 : fakeBase - Date.now()
    const interval = setInterval(() => {
      setNow(Date.now() + offset)
    }, 1000)
    return () => clearInterval(interval)
  }, [fakeBase])

  return now
}

export default useNow
