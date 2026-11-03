/** Which metro lines each line group covers, and which stations it includes. */
import type { LineGroup, Station } from "@/types/station";

/** Metro lines in each line group, in badge order. */
export const LINE_GROUP_ROUTES: Record<LineGroup, string[]> = {
  "M1/M2": ["M1", "M2"],
  "M3/M4": ["M3", "M4"],
};

/**
 * Return whether any area of the station serves a line in the group.
 *
 * An interchange whose areas serve lines from both groups appears under both.
 */
export function stationServesLineGroup(station: Station, lineGroup: LineGroup): boolean {
  return station.areas.some((area) =>
    area.line.some((line) => LINE_GROUP_ROUTES[lineGroup].includes(line)),
  );
}
