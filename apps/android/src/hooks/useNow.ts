// the wall clock, refreshed every second. countdowns recompute from a fresh
// now instead of trusting a duration, so the display stays honest even when the
// snapshot it came from is minutes old.
import { useEffect, useState } from "react";

const TICK_MS = 1000;

export function useNow(): number {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), TICK_MS);
    return () => clearInterval(id);
  }, []);

  return now;
}
