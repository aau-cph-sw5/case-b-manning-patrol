/**
 * React state for the trains SSE stream (position-interface/v2,
 * GET /api/v2/trains/stream), saved to localStorage so a reload shows the
 * last known state at once.
 */

import { useState, useEffect } from "react";
import type { TrainsUpdate } from "@/api/dashboardApi";
import { subscribeToTrains } from "@/api/dashboardApi";

/** localStorage key holding the last received TrainsUpdate as JSON. */
const LOCAL_STORAGE_KEY = "trainsState";

/**
 * Parse a stored TrainsUpdate; null for a missing or malformed value. The
 * shape is not checked.
 */
function parseStoredTrains(stored: string | null): TrainsUpdate | null {
  if (!stored) return null;
  try {
    return JSON.parse(stored) as TrainsUpdate;
  } catch {
    return null;
  }
}

/**
 * Connect to the trains SSE stream and return its latest state.
 *
 * Starts from the trains update saved in localStorage, if any. Every event
 * replaces the state and is saved to localStorage. Connects once on mount and
 * closes the connection on unmount.
 *
 * @returns
 * - `trainsUpdate`: the last received or saved update; null until either
 *   exists.
 * - `isLoading`: true until the first event or error, even while a saved
 *   update is shown.
 * - `error`: set on a connection error and cleared by the next event. The
 *   stream keeps reconnecting meanwhile, so an error is not final. Its
 *   message is always "SSE connection error", since error events carry no
 *   data.
 * - `lastUpdated`: the server's `time` of the shown update (ISO 8601), so a
 *   saved one keeps its original time; null without an update.
 */
export function useTrainStream(): {
  trainsUpdate: TrainsUpdate | null;
  isLoading: boolean;
  error: Error | null;
  lastUpdated: string | null;
} {
  const [trainsUpdate, setTrainsUpdate] = useState<TrainsUpdate | null>(() => {
    return parseStoredTrains(localStorage.getItem(LOCAL_STORAGE_KEY));
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    return subscribeToTrains(
      (newUpdate: TrainsUpdate) => {
        setTrainsUpdate(newUpdate);
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(newUpdate));
        setError(null);
        setIsLoading(false);
      },
      () => {
        setError(new Error("SSE connection error"));
        setIsLoading(false);
      }
    );
  }, []);

  return { trainsUpdate, isLoading, error, lastUpdated: trainsUpdate?.time || null };
}

/** Return the trains update saved by {@link useTrainStream}, or null, without connecting. */
export function getStoredTrains(): TrainsUpdate | null {
  return parseStoredTrains(localStorage.getItem(LOCAL_STORAGE_KEY));
}

/**
 * Remove the saved trains update from localStorage.
 *
 * A mounted {@link useTrainStream} keeps its in-memory state and saves again
 * on the next event.
 */
export function clearStoredTrains(): void {
  localStorage.removeItem(LOCAL_STORAGE_KEY);
}
