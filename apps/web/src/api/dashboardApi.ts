// Server-Sent Events stream for Dashboard updates
// position-interface/v2 contract: GET /api/v2/dashboard/stream

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/**
 * Area type as defined in position-interface/v2 contract
 */
export type AreaType = "platform" | "concourse";

/**
 * Patrol area belonging to a station
 */
export interface Area {
  area_id: string;
  name: string;
  line: string[];
  area_type: AreaType;
  covered_now: boolean;
  overdue_at: string | null; // ISO 8601 date-time with offset, or null
}

/**
 * Station with its patrol areas
 */
export interface Station {
  station_id: string;
  name: string;
  areas: Area[];
}

/**
 * Train information for the dashboard
 */
export interface Train {
  train_id: string; // UUID
  slug: string;
  total_time_secs: number;
  manned_time_secs: number;
  current_steward_ids: string[]; // UUIDs of stewards currently manning the train; empty when unmanned
  line: string[]; // e.g. ["M1", "M2"] — position-interface v2.4.0
}

/**
 * Complete dashboard state pushed via SSE on the dashboard stream (stations only)
 */
export interface Dashboard {
  stations: Station[];
  time: string; // ISO 8601 date-time with offset when server sent the event
}

/**
 * Train manning state pushed via SSE on the separate trains stream
 * (GET /api/v2/trains/stream, event "trains")
 */
export interface TrainsUpdate {
  trains: Train[];
  time: string; // ISO 8601 date-time with offset when server sent the event
}

/**
 * Error response type
 */
export interface ApiError {
  code: string;
  message: string;
}

/**
 * Connect to the dashboard SSE stream
 * Returns the EventSource instance for manual management
 */
export function connectDashboardStream(): EventSource {
  return new EventSource(`${API_BASE_URL}/api/v2/dashboard/stream`);
}

/**
 * Subscribe to dashboard updates with automatic parsing
 * @param callback - Called with each new Dashboard state
 * @returns EventSource instance - call .close() to disconnect
 */
export function subscribeToDashboard(
  callback: (dashboard: Dashboard) => void,
  onError?: (error: Event) => void
): EventSource {
  const eventSource = new EventSource(`${API_BASE_URL}/api/v2/dashboard/stream`);

  eventSource.addEventListener("dashboard", (event) => {
    try {
      const dashboard: Dashboard = JSON.parse(event.data);
      callback(dashboard);
    } catch (error) {
      console.error("Failed to parse dashboard event:", error);
    }
  });

  if (onError) {
    eventSource.onerror = onError;
  }

  return eventSource;
}
