import { useEffect, useState } from 'react'

/**
 * Return the current time in ms since epoch, re-rendering the caller once per
 * second.
 *
 * The interval is cleared on unmount.
 */
export function useNow(): number {
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const interval = setInterval(() => {
      setNow(Date.now())
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  return now
}

export default useNow
