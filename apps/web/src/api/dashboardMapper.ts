// Maps the dashboard SSE payload (position-interface/v2) to the view model
// consumed by Dashboard, StationCard, and TimeColor.

import type { AreaType, Dashboard } from "./dashboardApi"

export interface StationLevel {
  label: string
  overdueAt: number | null // epoch ms deadline; null means no deadline (manned or unknown)
  manned: boolean
}

export interface Station {
  stationId: string
  name: string
  levels: StationLevel[]
}

const AREA_LABELS: Record<AreaType, string> = {
  platform: "Perron",
  concourse: "Forhal",
}

function areaLabel(areas: { area_type: AreaType }[], index: number): string {
  const kind = areas[index].area_type
  const ofSameKind = areas.filter((area) => area.area_type === kind).length
  if (ofSameKind <= 1) {
    return AREA_LABELS[kind]
  }
  const ordinal = areas.slice(0, index + 1).filter((area) => area.area_type === kind).length
  return `${AREA_LABELS[kind]} ${ordinal}`
}

export function toViewStations(dashboard: Dashboard): Station[] {
  return dashboard.stations.map((station) => ({
    stationId: station.station_id,
    name: station.name,
    levels: station.areas.map((area, index) => ({
      label: areaLabel(station.areas, index),
      overdueAt: area.overdue_at ? Date.parse(area.overdue_at) : null,
      manned: area.covered_now,
    })),
  }))
}
