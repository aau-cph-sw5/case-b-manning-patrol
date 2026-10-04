// milliseconds since startedAt, refreshed every second. 0 while there is no start time.
import { useEffect, useState } from "react";

const TICK_MS = 1000;

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
