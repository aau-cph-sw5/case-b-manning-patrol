import { useEffect, useState } from "react";

const TICK_MS = 1000;

/**
 * Return the wall clock in ms since epoch, re-rendering the caller every
 * second.
 *
 * Countdowns recompute from a fresh now instead of trusting a duration, so
 * the display stays honest even when the snapshot it came from is minutes
 * old. The interval is cleared on unmount.
 */
export function useNow(): number {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), TICK_MS);
    return () => clearInterval(id);
  }, []);

  return now;
}
