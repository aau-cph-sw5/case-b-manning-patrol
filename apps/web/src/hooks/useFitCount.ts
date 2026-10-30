import { type RefObject, useEffect, useLayoutEffect, useState } from 'react'

/**
 * Return how many rows of the list fit in its visible height.
 *
 * Assumes every row is as tall as the first child. Returns `Infinity` until a
 * first row exists to measure, never less than 1 after that, and keeps the
 * last value while the list is empty. Re-measures after every render and when
 * the list resizes; the `ResizeObserver` is disconnected on the next render
 * and on unmount.
 */
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
