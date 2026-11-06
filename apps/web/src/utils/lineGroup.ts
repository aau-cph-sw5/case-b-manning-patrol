// Line groups as on the Android app: the dashboard filters stations by metro line group.

export type LineGroup = 'M1/M2' | 'M3/M4'

export const LINE_GROUPS: LineGroup[] = ['M1/M2', 'M3/M4']

export const LINE_GROUP_ROUTES: Record<LineGroup, string[]> = {
  'M1/M2': ['M1', 'M2'],
  'M3/M4': ['M3', 'M4'],
}

// route badge colors, same as the Android app (Station.tsx routeColors)
export const ROUTE_COLORS: Record<string, string> = {
  M1: '#007D55',
  M2: '#FFC82D',
  M3: '#E6140F',
  M4: '#00A0BE',
}

export function stationServesLineGroup(
  station: { lines: string[] },
  lineGroup: LineGroup,
): boolean {
  return station.lines.some((line) => LINE_GROUP_ROUTES[lineGroup].includes(line))
}
