import type { LineGroup, StationRecord } from "@/types/station";

export const LINE_GROUP_ROUTES: Record<LineGroup, string[]> = {
  "M1/M2": ["M1", "M2"],
  "M3/M4": ["M3", "M4"],
};

export function stationServesLineGroup(station: StationRecord, lineGroup: LineGroup): boolean {
  return LINE_GROUP_ROUTES[lineGroup].some((route) => station.routeCodes?.includes(route));
}
