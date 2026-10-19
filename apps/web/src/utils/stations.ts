import type { Station as ApiStation } from '../data/stationsApi'
import type { Station } from '../data/mockData'

// Placeholder indtil connect/disconnect-events findes: alle områder
// starter som ikke-patruljeret, timeren tæller ned fra nu.
function initialLevelStatus(): { lastPatrolAt: number; manned: boolean } {
  return { lastPatrolAt: Date.now(), manned: false }
}

export function toStationCardData(station: ApiStation): Station {
  return {
    code: station.id,
    name: station.name,
    levels: station.patrol_areas.map((area) => ({
      label: area.kind[0].toUpperCase() + area.kind.slice(1),
      beaconId: area.beacon_id,
      ...initialLevelStatus(),
    })),
  }
}
