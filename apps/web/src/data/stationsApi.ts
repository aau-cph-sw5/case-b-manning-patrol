// Types matching the response from GET /api/v2/stations on the backend.
// Keep these in sync with StationOut and AreaOut in services/api.

export type AreaKind = 'platform' | 'concourse'

export interface PatrolArea {
  kind: AreaKind
  beacon_id: string
}

export interface ApiStation {
  id: string
  name: string
  patrol_areas: PatrolArea[]
}
