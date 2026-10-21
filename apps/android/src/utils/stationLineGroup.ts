import type { LineGroup, StationRecord } from "@/types/station";

// the route codes that make up each line group. shared by the filter (matching a
// station to the selected group) and the filter's chips (the badges it shows).
export const LINE_GROUP_ROUTES: Record<LineGroup, string[]> = {
  "M1/M2": ["M1", "M2"],
  "M3/M4": ["M3", "M4"],
};

// temporary stand-in for the backend feed: the backend will tag each area with its
// line group, but until that contract lands the mock fixtures carry individual route
// codes, so a station serves a group when any of its routes belongs to it.
export function stationServesLineGroup(station: StationRecord, lineGroup: LineGroup): boolean {
  return LINE_GROUP_ROUTES[lineGroup].some((route) => station.routeCodes?.includes(route));
}
