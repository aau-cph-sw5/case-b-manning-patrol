// Line groups as on the Android app: the dashboard filters stations by metro line group.

export type LineGroup = 'M1/M2' | 'M3/M4'

export const LINE_GROUPS: LineGroup[] = ['M1/M2', 'M3/M4']

/** Filter selection: one line group, or every line at once (the composed view). */
export type LineGroupSelection = LineGroup | 'ALL'

/** Selectable segments of the line filter; 'ALL' comes first as the default view. */
export const LINE_GROUP_SELECTIONS: LineGroupSelection[] = ['ALL', ...LINE_GROUPS]

export const LINE_GROUP_ROUTES: Record<LineGroup, string[]> = {
  'M1/M2': ['M1', 'M2'],
  'M3/M4': ['M3', 'M4'],
}

/** Every metro route, used for the 'ALL' selection. */
export const ALL_ROUTES: string[] = ['M1', 'M2', 'M3', 'M4']

// route badge colors, same as the Android app (Station.tsx routeColors)
export const ROUTE_COLORS: Record<string, string> = {
  M1: '#007D55',
  M2: '#FFC82D',
  M3: '#E6140F',
  M4: '#00A0BE',
}

/** Return the routes a selection covers: all four for 'ALL', else the group's. */
export function selectionRoutes(selection: LineGroupSelection): string[] {
  return selection === 'ALL' ? ALL_ROUTES : LINE_GROUP_ROUTES[selection]
}

/** Return whether the station is part of the selection; 'ALL' includes every station. */
export function stationServesLineGroup(
  station: { lines: string[] },
  selection: LineGroupSelection,
): boolean {
  if (selection === 'ALL') return true
  return station.lines.some((line) => LINE_GROUP_ROUTES[selection].includes(line))
}
