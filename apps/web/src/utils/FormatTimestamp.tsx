/** Formatting of the dashboard's "last updated" time. */

/**
 * Format an ISO 8601 timestamp in Danish as day, short month and time with
 * seconds, in the browser's time zone.
 *
 * Returns "Ingen data endnu" for null or an empty string; a string that does
 * not parse gives "Invalid Date".
 */
export function formatTimestamp(timeString: string | null): string {
  if (!timeString) return "Ingen data endnu";
  return new Date(timeString).toLocaleString("da-DK", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    day: "numeric",
    month: "short",
  });
}