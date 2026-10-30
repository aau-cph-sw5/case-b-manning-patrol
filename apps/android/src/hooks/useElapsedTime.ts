import { useEffect, useState } from "react";

const TICK_MS = 1000;

/**
 * Return the milliseconds since `startedAt`, re-rendering the caller every
 * second.
 *
 * Returns 0 while `startedAt` is null, and never a negative value. The
 * interval only runs while there is a start time; it is cleared when
 * `startedAt` changes and on unmount.
 *
 * @param startedAt - Start time in ms since epoch, or null for no session.
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
