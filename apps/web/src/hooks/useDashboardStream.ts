/**
 * React state for the dashboard SSE stream (position-interface/v2), saved to
 * localStorage so a reload shows the last known state at once.
 */

import { useState, useEffect, useRef } from "react";
import type { Dashboard } from "@/api/dashboardApi";
import { subscribeToDashboard } from "@/api/dashboardApi";

/** localStorage key holding the last received Dashboard as JSON. */
const LOCAL_STORAGE_KEY = "dashboardState";

/**
 * Parse a stored Dashboard; null for a missing or malformed value. The shape
 * is not checked.
 */
function parseStoredDashboard(stored: string | null): Dashboard | null {
  if (!stored) return null;
  try {
    return JSON.parse(stored) as Dashboard;
  } catch {
    return null;
  }
}

/**
 * Connect to the dashboard SSE stream and return its latest state.
 *
 * Starts from the dashboard saved in localStorage, if any. Every event
 * replaces the state and is saved to localStorage. Connects once on mount and
 * closes the connection on unmount.
 *
 * @returns
 * - `dashboard`: the last received or saved state; null until either exists.
 * - `isLoading`: true until the first event or error, even while a saved
 *   dashboard is shown.
 * - `error`: set on a connection error and cleared by the next event. The
 *   browser keeps reconnecting meanwhile, so an error is not final. Its
 *   message is always "SSE connection error", since error events carry no
 *   data.
 * - `lastUpdated`: the server's `time` of the shown dashboard (ISO 8601), so a
 *   saved one keeps its original time; null without a dashboard.
 */
export function useDashboardStream(): {
  dashboard: Dashboard | null;
  isLoading: boolean;
  error: Error | null;
  lastUpdated: string | null;
} {
  const [dashboard, setDashboard] = useState<Dashboard | null>(() => {
    return parseStoredDashboard(localStorage.getItem(LOCAL_STORAGE_KEY));
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    eventSourceRef.current = subscribeToDashboard(
      (newDashboard: Dashboard) => {
        setDashboard(newDashboard);
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(newDashboard));
        setError(null);
        setIsLoading(false);
      },
      (event: Event) => {
        setError(new Error((event as MessageEvent).data || "SSE connection error"));
        setIsLoading(false);
      }
    );

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, []);

  return { dashboard, isLoading, error, lastUpdated: dashboard?.time || null };
}

/** Return the dashboard saved by {@link useDashboardStream}, or null, without connecting. */
export function getStoredDashboard(): Dashboard | null {
  return parseStoredDashboard(localStorage.getItem(LOCAL_STORAGE_KEY));
}

/**
 * Remove the saved dashboard from localStorage.
 *
 * A mounted {@link useDashboardStream} keeps its in-memory state and saves
 * again on the next event.
 */
export function clearStoredDashboard(): void {
  localStorage.removeItem(LOCAL_STORAGE_KEY);
}
