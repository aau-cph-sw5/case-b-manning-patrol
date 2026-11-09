/** Hook measuring how many list rows fit in the visible height. */
import { type RefObject, useEffect, useLayoutEffect, useState } from 'react'

/**
 * Return how many rows of a list fit in its visible height.
 *
 * Divides the list's `clientHeight` by the height of its first row, so every
 * row is assumed to be as tall as the first. Returns Infinity until a row has
 * been measured and at least 1 after that. Measures again after every render,
 * since rows can appear after the first one, and whenever the list resizes.
 * The ResizeObserver is replaced after every render and disconnected on
 * unmount.
 *
 * @param ref - The list element; its children are the rows.
 */
export function useFitCount(ref: RefObject<HTMLElement | null>): number {
  const [fit, setFit] = useState(Infinity)

  const measure = () => {
    const list = ref.current
    const row = list?.firstElementChild as HTMLElement | null | undefined
    if (!list || !row) return
    setFit(Math.max(1, Math.floor(list.clientHeight / row.offsetHeight)))
  }

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
