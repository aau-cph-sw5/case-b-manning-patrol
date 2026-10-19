import { useEffect, useState } from 'react'

// current time in ms, re-rendering the caller once per second
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
