import type { LineGroup, Station } from "@/types/station";

export const LINE_GROUP_ROUTES: Record<LineGroup, string[]> = {
  "M1/M2": ["M1", "M2"],
  "M3/M4": ["M3", "M4"],
};

export function stationServesLineGroup(station: Station, lineGroup: LineGroup): boolean {
  return station.areas.some((area) =>
    LINE_GROUP_ROUTES[lineGroup].includes(area.line),
  );
}
