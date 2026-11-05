/**
 * Maps the dashboard SSE payload (position-interface/v2) to the view model
 * consumed by Dashboard, StationCard, and TimeColor.
 */

import type { AreaType, Dashboard } from "./dashboardApi"

/** One patrol area as the dashboard shows it. */
export interface StationLevel {
  /** Danish display label, e.g. "Perron", or "Perron 2" when a station has several of a kind. */
  label: string
  /** Deadline in epoch ms; null means no deadline (manned, or never patrolled). */
  overdueAt: number | null
  /** True while a steward is patrolling the area right now. */
  manned: boolean
}

/** A station as the dashboard shows it. */
export interface Station {
  stationId: string
  name: string
  lines: string[] 
  levels: StationLevel[]
}

const AREA_LABELS: Record<AreaType, string> = {
  platform: "Perron",
  concourse: "Forhal",
}

/**
 * Return the Danish label for the area at `index`, numbered by position among
 * its kind ("Perron 1", "Perron 2") only when the station has more than one.
 */
function areaLabel(areas: { area_type: AreaType }[], index: number): string {
  const kind = areas[index].area_type
  const ofSameKind = areas.filter((area) => area.area_type === kind).length
  if (ofSameKind <= 1) {
    return AREA_LABELS[kind]
  }
  const ordinal = areas.slice(0, index + 1).filter((area) => area.area_type === kind).length
  return `${AREA_LABELS[kind]} ${ordinal}`
}

/**
 * Map a dashboard event to the stations the dashboard renders.
 *
 * Keeps the order of stations and areas, drops the trains, and parses
 * `overdue_at` to epoch ms. An unparseable timestamp becomes NaN, not null.
 */
export function toViewStations(dashboard: Dashboard): Station[] {
  return dashboard.stations.map((station) => ({
    stationId: station.station_id,
    name: station.name,
    lines: [...new Set(station.areas.flatMap((area) => area.line))],
    levels: station.areas.map((area, index) => ({
      label: areaLabel(station.areas, index),
      overdueAt: area.overdue_at ? Date.parse(area.overdue_at) : null,
      manned: area.covered_now,
    })),
  }))
}
