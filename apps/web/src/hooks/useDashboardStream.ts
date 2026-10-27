// React hook for managing dashboard SSE stream state with local persistence
// position-interface/v2 contract

import { useState, useEffect, useRef } from "react";
import type { Dashboard } from "@/api/dashboardApi";
import { connectDashboardStream, subscribeToDashboard } from "@/api/dashboardApi";

const LOCAL_STORAGE_KEY = "dashboardState";

/**
 * Parse stored dashboard JSON from localStorage
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
 * React hook that connects to the dashboard SSE stream and maintains state
 * @returns Current dashboard state, loading status, and error
 */
export function useDashboardStream(): {
  dashboard: Dashboard | null;
  isLoading: boolean;
  error: Error | null;
} {
  const [dashboard, setDashboard] = useState<Dashboard | null>(() => {
    // Initialize from localStorage if available
    return parseStoredDashboard(localStorage.getItem(LOCAL_STORAGE_KEY));
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    setIsLoading(true);
    setError(null);

    // Connect to SSE stream
    eventSourceRef.current = subscribeToDashboard(
      (newDashboard: Dashboard) => {
        // Save to both state and localStorage
        setDashboard(newDashboard);
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(newDashboard));
        setIsLoading(false);
      },
      (event: Event) => {
        // Handle errors - but SSE auto-reconnects in most browsers
        setError(new Error((event as MessageEvent).data || "SSE connection error"));
        setIsLoading(false);
      }
    );

    // Cleanup on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, []);

  return { dashboard, isLoading, error };
}

/**
 * Get the current dashboard state from localStorage (without connecting to stream)
 */
export function getStoredDashboard(): Dashboard | null {
  return parseStoredDashboard(localStorage.getItem(LOCAL_STORAGE_KEY));
}

/**
 * Clear stored dashboard state from localStorage
 */
export function clearStoredDashboard(): void {
  localStorage.removeItem(LOCAL_STORAGE_KEY);
}
