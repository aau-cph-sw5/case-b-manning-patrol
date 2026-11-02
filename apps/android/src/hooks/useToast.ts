// holds the toast currently on screen: a new message replaces the old one and
// restarts the hide timer. null means no toast is showing.
import { useEffect, useRef, useState } from "react";

import { subscribeToToasts } from "@/state/toast";

const TOAST_DURATION_MS = 4_000;

export function useToast(): string | null {
  const [message, setMessage] = useState<string | null>(null);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const unsubscribe = subscribeToToasts((next) => {
      setMessage(next);
      if (hideTimerRef.current !== null) {
        clearTimeout(hideTimerRef.current);
      }
      hideTimerRef.current = setTimeout(() => setMessage(null), TOAST_DURATION_MS);
    });

    return () => {
      unsubscribe();
      if (hideTimerRef.current !== null) {
        clearTimeout(hideTimerRef.current);
      }
    };
  }, []);

  return message;
}
