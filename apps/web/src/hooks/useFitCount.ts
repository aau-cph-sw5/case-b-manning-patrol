import { type RefObject, useEffect, useLayoutEffect, useState } from 'react'

// Takes the height of the first row and measures how many can fit before cutoff
export function useFitCount(ref: RefObject<HTMLElement | null>): number {
  const [fit, setFit] = useState(Infinity)

  const measure = () => {
    const list = ref.current
    const row = list?.firstElementChild as HTMLElement | null | undefined
    if (!list || !row) return
    setFit(Math.max(1, Math.floor(list.clientHeight / row.offsetHeight)))
  }

  // rows can appear after the first render, so check after every render
  useLayoutEffect(measure)

  useEffect(() => {
    if (!ref.current) return
    const observer = new ResizeObserver(measure)
    observer.observe(ref.current)
    return () => observer.disconnect()
  })

  return fit
}

export default useFitCount
