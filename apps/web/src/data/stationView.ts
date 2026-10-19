// View-model types for the station dashboard. Built from the API's
// Station type by toStationCardData in utils/stations.

export interface StationLevel {
  label: string
  beaconId: string
  lastPatrolAt: number
  manned: boolean
}

export interface Station {
  code: string
  name: string
  levels: StationLevel[]
}
