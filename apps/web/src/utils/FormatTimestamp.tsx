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