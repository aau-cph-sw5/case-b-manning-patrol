/** Hook for a live elapsed-time counter. */
import { useEffect, useState } from "react";

const TICK_MS = 1000;

/**
 * Return the milliseconds since `startedAt`, refreshed every second.
 *
 * Returns 0 and runs no timer while `startedAt` is null. The interval restarts
 * when `startedAt` changes and is cleared on unmount. Never negative, even if
 * the device clock moves backwards.
 */
export function useElapsedTime(startedAt: number | null): number {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (startedAt === null) return;
    const id = setInterval(() => setNow(Date.now()), TICK_MS);
    return () => clearInterval(id);
  }, [startedAt]);

  if (startedAt === null) return 0;
  return Math.max(0, now - startedAt);
}
